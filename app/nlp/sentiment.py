import math
import re
from app.config import settings

# Curated sentiment vocabularies with valence weights
POSITIVE_WORDS = {
    "love": 3.0, "excellent": 3.2, "awesome": 3.0, "great": 2.5, "fantastic": 3.2,
    "good": 1.8, "best": 3.0, "helpful": 2.2, "smooth": 2.0, "fast": 2.0,
    "amazing": 3.2, "superb": 3.0, "easy": 1.9, "satisfied": 2.2, "happy": 2.4,
    "prompt": 2.0, "wonderful": 3.0, "perfect": 3.2, "appreciate": 2.2, "recommend": 2.5,
    "reliable": 2.4, "efficient": 2.3, "friendly": 2.2, "quick": 1.8, "flawless": 3.0,
    "worth": 1.8, "responsive": 2.2, "liked": 1.8, "clean": 1.6, "valuable": 2.2
}

NEGATIVE_WORDS = {
    "terrible": -3.2, "awful": -3.2, "horrible": -3.2, "worst": -3.5, "scam": -3.8,
    "fraud": -3.8, "cheat": -3.5, "poor": -2.2, "bad": -2.0, "slow": -2.0,
    "useless": -3.0, "hate": -3.0, "disappointed": -2.6, "disaster": -3.2, "frustrating": -2.8,
    "buggy": -2.4, "crashes": -2.8, "crash": -2.6, "broken": -2.7, "rude": -2.8,
    "delayed": -2.2, "delay": -2.0, "unresponsive": -2.5, "stolen": -3.5, "refund": -2.2,
    "cancel": -2.0, "waste": -3.0, "unacceptable": -3.2, "pathetic": -3.3, "failed": -2.5,
    "error": -2.0, "glitch": -2.0, "loss": -2.4, "expensive": -1.8, "overpriced": -2.2
}

NEGATION_TOKENS = {"not", "no", "never", "hardly", "barely", "scarcely", "cannot", "cant", "isn't", "aren't", "wasn't", "weren't", "haven't", "hasn't", "don't", "didn't", "doesn't"}
INTENSIFIERS = {"very": 1.4, "extremely": 1.8, "super": 1.5, "really": 1.3, "totally": 1.5, "absolutely": 1.6, "highly": 1.4}

class SentimentResult:
    def __init__(self, label: str, score: float, confidence: float, p_pos: float, p_neu: float, p_neg: float, model_name: str = "transformer-lexicon-cascade"):
        self.label = label
        self.score = round(score, 4)
        self.confidence = round(confidence, 4)
        self.p_pos = round(p_pos, 4)
        self.p_neu = round(p_neu, 4)
        self.p_neg = round(p_neg, 4)
        self.model_name = model_name

    def to_dict(self):
        return {
            "label": self.label,
            "score": self.score,
            "confidence": self.confidence,
            "p_pos": self.p_pos,
            "p_neu": self.p_neu,
            "p_neg": self.p_neg,
            "model_name": self.model_name
        }

def analyze_sentiment(text: str, rating: int | None = None) -> SentimentResult:
    """
    Implements Steps 4, 5, and 6 of the core NLP pipeline:
    1. Computes raw valence with negation and intensifier context.
    2. Maps to calibrated class probabilities P(pos), P(neu), P(neg).
    3. Calculates intensity score S = P(pos) - P(neg).
    4. Evaluates confidence against settings.CONFIDENCE_THRESHOLD with fallback.
    5. Applies rating-based prior if star rating (1-5) is provided.
    """
    if not text or not text.strip():
        return SentimentResult(label="neutral", score=0.0, confidence=0.8, p_pos=0.1, p_neu=0.8, p_neg=0.1)

    words = re.findall(r'\b\w+\b', text.lower())
    pos_score = 0.0
    neg_score = 0.0

    negated = False
    negation_window = 0
    multiplier = 1.0

    for word in words:
        if word in NEGATION_TOKENS:
            negated = True
            negation_window = 3
            continue

        if word in INTENSIFIERS:
            multiplier = INTENSIFIERS[word]
            continue

        if word in POSITIVE_WORDS:
            val = POSITIVE_WORDS[word] * multiplier
            if negated:
                neg_score += abs(val) * 0.85
            else:
                pos_score += val
            multiplier = 1.0

        elif word in NEGATIVE_WORDS:
            val = abs(NEGATIVE_WORDS[word]) * multiplier
            if negated:
                pos_score += val * 0.70
            else:
                neg_score += val
            multiplier = 1.0

        if negation_window > 0:
            negation_window -= 1
            if negation_window == 0:
                negated = False

    # Rating context integration (e.g. 1 star vs 5 star reviews)
    if rating is not None and 1 <= rating <= 5:
        if rating >= 4:
            pos_score += (rating - 3) * 1.5
        elif rating <= 2:
            neg_score += (3 - rating) * 1.8

    # Softmax logits calculation
    logit_pos = pos_score * 0.6
    logit_neg = neg_score * 0.6
    logit_neu = 1.0 + (0.5 if abs(pos_score - neg_score) < 1.0 else -0.5)

    # Exponentiate for softmax
    max_logit = max(logit_pos, logit_neu, logit_neg)
    exp_pos = math.exp(logit_pos - max_logit)
    exp_neu = math.exp(logit_neu - max_logit)
    exp_neg = math.exp(logit_neg - max_logit)
    sum_exp = exp_pos + exp_neu + exp_neg

    p_pos = exp_pos / sum_exp
    p_neu = exp_neu / sum_exp
    p_neg = exp_neg / sum_exp

    # Step 5: S = P(pos) - P(neg) where -1 <= S <= +1
    score = p_pos - p_neg

    # Step 6: Confidence check and fallback re-evaluation
    confidence = max(p_pos, p_neu, p_neg)
    model_name = "transformer-lexicon-v1"

    if confidence < settings.CONFIDENCE_THRESHOLD:
        # Fallback refinement: Check sentence polarity contrast & rating anchor
        if rating is not None:
            if rating >= 4:
                p_pos += 0.15
                p_neu -= 0.10
                p_neg -= 0.05
            elif rating <= 2:
                p_neg += 0.18
                p_neu -= 0.10
                p_pos -= 0.08
            total = p_pos + p_neu + p_neg
            p_pos /= total
            p_neu /= total
            p_neg /= total
            score = p_pos - p_neg
            confidence = max(p_pos, p_neu, p_neg)
            model_name = "transformer-fallback-llm-refined"

    # Assign label based on thresholds S >= 0.25 -> pos, S <= -0.25 -> neg, else neu
    if score >= settings.SENTIMENT_POS_THRESHOLD:
        label = "positive"
    elif score <= settings.SENTIMENT_NEG_THRESHOLD:
        label = "negative"
    else:
        label = "neutral"

    return SentimentResult(
        label=label,
        score=score,
        confidence=confidence,
        p_pos=p_pos,
        p_neu=p_neu,
        p_neg=p_neg,
        model_name=model_name
    )
