from datetime import datetime
from pydantic import BaseModel

# User Schemas
class UserBase(BaseModel):
    name: str
    email: str
    role: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    user_id: int
    created_at: datetime
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: str
    password: str

# Source Schemas
class SourceBase(BaseModel):
    name: str
    source_type: str
    api_config: str | None = "{}"

class SourceCreate(SourceBase):
    user_id: int = 1

class SourceResponse(SourceBase):
    source_id: int
    user_id: int
    status: str
    last_synced_at: datetime | None = None
    class Config:
        from_attributes = True

# Sentiment & Theme Schemas
class SentimentLogResponse(BaseModel):
    log_id: int
    label: str
    score: float
    confidence: float
    p_pos: float
    p_neu: float
    p_neg: float
    model_name: str
    processed_at: datetime
    class Config:
        from_attributes = True

class ThemeResponse(BaseModel):
    theme_id: int
    label: str
    keywords: str
    created_at: datetime
    class Config:
        from_attributes = True

# Feedback Schemas
class FeedbackCreate(BaseModel):
    source_id: int
    text: str
    rating: int | None = None
    external_id: str | None = None

class FeedbackItemResponse(BaseModel):
    feedback_id: int
    source_id: int
    theme_id: int | None
    external_id: str | None
    text: str
    cleaned_text: str
    rating: int | None
    language: str
    urgency_score: float
    status: str
    created_at: datetime
    sentiment_log: SentimentLogResponse | None = None
    theme: ThemeResponse | None = None
    source_name: str | None = None
    class Config:
        from_attributes = True

class FeedbackStatusUpdate(BaseModel):
    status: str  # "new", "in_progress", "resolved"

# Alert Schemas
class AlertResponse(BaseModel):
    alert_id: int
    user_id: int
    source_id: int | None
    alert_type: str
    severity: str
    message: str
    channel: str
    status: str
    triggered_at: datetime
    class Config:
        from_attributes = True

class AlertStatusUpdate(BaseModel):
    status: str  # "active", "acknowledged", "resolved"
