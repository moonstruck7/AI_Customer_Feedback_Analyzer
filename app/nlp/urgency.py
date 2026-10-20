import re
from app.config import settings

def calculate_urgency(text: str, sentiment_score: float, rating: int | None = None) -> tuple[float, bool, list[str]]:
    """
    Implements Step 9 of the algorithm:
    - Analyzes critical keywords ('refund', 'scam', 'fraud', 'cancel', 'lawsuit', 'unsafe', etc.)
    - Assesses sentiment intensity score S (especially if S <= -0.70)
    - Returns (urgency_score [0-100], is_urgent [bool], matched_keywords [list])
    """
    if not text:
        return 0.0, False, []

    text_lower = text.lower()
    matched = []
    urgency = 0.0

    for kw in settings.CRITICAL_KEYWORDS:
        if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
            matched.append(kw)
            urgency += 25.0

    # Negative sentiment contribution
    if sentiment_score <= settings.URGENCY_NEGATIVE_CUTOFF:
        urgency += 45.0
    elif sentiment_score <= -0.40:
        urgency += 25.0
    elif sentiment_score <= -0.25:
        urgency += 10.0

    # Low rating contribution
    if rating == 1:
        urgency += 20.0
    elif rating == 2:
        urgency += 10.0

    # Cap score at 100
    urgency = min(100.0, round(urgency, 1))
    is_urgent = urgency >= 60.0 or len(matched) >= 2 or (sentiment_score <= -0.75 and urgency >= 50.0)

    return urgency, is_urgent, matched
