import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Standard recurring themes with representative seed anchors and keywords
DEFAULT_THEME_DEFINITIONS = [
    {
        "label": "App Bugs & Performance",
        "keywords": "crash, bug, slow, lag, update, error, freeze, glitch, battery, battery drain, loading",
        "seeds": [
            "the app crashes every time I open it",
            "screen freezes and shows an unexpected error",
            "extremely slow loading and huge lag after the recent update",
            "constant glitches and application keeps closing unexpectedly"
        ]
    },
    {
        "label": "Billing & Refund Issues",
        "keywords": "charge, refund, money, billing, payment, subscription, deduction, invoice, scam, unauthorized",
        "seeds": [
            "charged twice on my credit card without confirmation",
            "demanded a refund but support refused to return my money",
            "subscription renewed automatically even after cancellation",
            "payment failed but money deducted from bank account"
        ]
    },
    {
        "label": "Delivery & Logistics",
        "keywords": "delivery, late, courier, delay, package, tracking, arrived, damaged, dispatch, shipping",
        "seeds": [
            "order delayed for over two weeks with no tracking update",
            "package arrived completely broken and damaged",
            "delivery executive was unresponsive and marked undelivered",
            "shipping takes forever compared to promised estimated date"
        ]
    },
    {
        "label": "Customer Support & Staff",
        "keywords": "support, agent, rude, unhelpful, ticket, call, waiting, response, staff, attitude",
        "seeds": [
            "customer care agent was rude and hung up on me",
            "support ticket has been pending for five days without response",
            "unhelpful staff who had no idea how to resolve my issue",
            "called helpline multiple times and stayed on hold for hours"
        ]
    },
    {
        "label": "Product Quality & Usability",
        "keywords": "quality, interface, navigation, broken, features, design, complicated, confusing, materials",
        "seeds": [
            "user interface is confusing and very difficult to navigate",
            "missing essential features that were promised in advertisement",
            "poor material quality and defective product",
            "design looks cluttered and search functionality is ineffective"
        ]
    }
]

class ThemeEngine:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=2500, stop_words="english", ngram_range=(1, 2))
        self.theme_labels: list[str] = []
        self.theme_keywords: dict[str, str] = {}
        self.theme_centroids: np.ndarray | None = None
        self._initialise_themes()

    def _initialise_themes(self):
        all_seed_docs = []
        theme_index_map = []

        for idx, theme in enumerate(DEFAULT_THEME_DEFINITIONS):
            label = theme["label"]
            self.theme_labels.append(label)
            self.theme_keywords[label] = theme["keywords"]
            for s in theme["seeds"]:
                all_seed_docs.append(s + " " + theme["keywords"])
                theme_index_map.append(idx)

        # Fit TF-IDF on seed texts
        self.tfidf_matrix = self.vectorizer.fit_transform(all_seed_docs)
        
        # Calculate centroids for each predefined theme
        centroids = []
        theme_index_map = np.array(theme_index_map)
        for idx in range(len(DEFAULT_THEME_DEFINITIONS)):
            mask = (theme_index_map == idx)
            cluster_vectors = self.tfidf_matrix[mask].toarray()
            centroid = np.mean(cluster_vectors, axis=0)
            # Normalize centroid
            norm = np.linalg.norm(centroid)
            if norm > 0:
                centroid = centroid / norm
            centroids.append(centroid)

        self.theme_centroids = np.array(centroids)

    def assign_theme(self, text: str, min_similarity: float = 0.08) -> tuple[str, str, float]:
        """
        Assigns text to closest theme centroid using cosine similarity and keyword heuristics.
        Returns: (theme_label, keywords, similarity_score)
        """
        if not text or not text.strip():
            return "General Feedback", "feedback, service, opinion", 0.0

        text_lower = text.lower()
        # Direct keyword priority check
        for idx, t_def in enumerate(DEFAULT_THEME_DEFINITIONS):
            kws = [k.strip() for k in t_def["keywords"].split(",") if k.strip()]
            for kw in kws:
                if kw in text_lower:
                    label = t_def["label"]
                    return label, self.theme_keywords.get(label, ""), 0.85

        vec = self.vectorizer.transform([text]).toarray()
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm

        sims = cosine_similarity(vec, self.theme_centroids)[0]
        best_idx = int(np.argmax(sims))
        best_score = float(sims[best_idx])

        if best_score >= min_similarity:
            label = self.theme_labels[best_idx]
            keywords = self.theme_keywords.get(label, "")
            return label, keywords, best_score
        else:
            return "General Feedback", "experience, comments, miscellaneous", best_score

theme_engine = ThemeEngine()
