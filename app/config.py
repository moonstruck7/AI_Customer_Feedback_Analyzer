import os
from pydantic import BaseModel

class Settings(BaseModel):
    APP_NAME: str = "AI Customer Feedback Analyzer"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./feedback_analyzer.db")
    
    # NLP & Anomaly Detection Parameters (From Section 7.1)
    SENTIMENT_POS_THRESHOLD: float = 0.25   # S >= 0.25 is positive
    SENTIMENT_NEG_THRESHOLD: float = -0.25  # S <= -0.25 is negative
    CONFIDENCE_THRESHOLD: float = 0.60     # Below this, fallback logic re-evaluates
    
    URGENCY_NEGATIVE_CUTOFF: float = -0.70  # S <= -0.70 triggers high urgency boost
    CRITICAL_KEYWORDS: list[str] = [
        "refund", "scam", "fraud", "cancel", "unsafe", "sue", "lawsuit", 
        "cheat", "stolen", "terrible", "worst", "unacceptable", "broken"
    ]
    
    # Statistical Anomaly Detection (Section 7.1 Step 11)
    ANOMALY_Z_SCORE_THRESHOLD: float = 2.5
    MIN_DAILY_FEEDBACK_VOLUME: int = 5
    ROLLING_BASELINE_DAYS: int = 28
    
    # Alerts delivery simulation / webhooks
    SLACK_WEBHOOK_URL: str = os.getenv("SLACK_WEBHOOK_URL", "")
    SMTP_ENABLED: bool = False

settings = Settings()
