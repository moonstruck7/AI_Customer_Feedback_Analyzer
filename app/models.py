from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="SMB Owner")  # SMB Owner, Support Manager, System Admin
    created_at = Column(DateTime, default=utc_now)

    sources = relationship("Source", back_populates="owner", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")

class Source(Base):
    __tablename__ = "sources"

    source_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    source_type = Column(String(50), nullable=False)  # google_play, google_business, helpdesk, survey, csv
    name = Column(String(100), nullable=False)
    api_config = Column(Text, default="{}")
    status = Column(String(30), default="active")  # active, paused, error
    last_synced_at = Column(DateTime, nullable=True)

    owner = relationship("User", back_populates="sources")
    feedback_items = relationship("FeedbackItem", back_populates="source", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="source", cascade="all, delete-orphan")

class Theme(Base):
    __tablename__ = "themes"

    theme_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    label = Column(String(100), unique=True, nullable=False)
    keywords = Column(Text, default="")
    created_at = Column(DateTime, default=utc_now)

    feedback_items = relationship("FeedbackItem", back_populates="theme")

class FeedbackItem(Base):
    __tablename__ = "feedback_items"

    feedback_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("sources.source_id"), nullable=False)
    theme_id = Column(Integer, ForeignKey("themes.theme_id"), nullable=True)
    external_id = Column(String(128), index=True, nullable=True)  # Hash for deduplication
    text = Column(Text, nullable=False)
    cleaned_text = Column(Text, nullable=False)
    rating = Column(Integer, nullable=True)  # 1 to 5 star rating if available
    language = Column(String(20), default="en")
    urgency_score = Column(Float, default=0.0)  # 0 to 100
    status = Column(String(30), default="new")  # new, in_progress, resolved
    created_at = Column(DateTime, default=utc_now)
    ingested_at = Column(DateTime, default=utc_now)

    source = relationship("Source", back_populates="feedback_items")
    theme = relationship("Theme", back_populates="feedback_items")
    sentiment_log = relationship("SentimentLog", back_populates="feedback_item", uselist=False, cascade="all, delete-orphan")

class SentimentLog(Base):
    __tablename__ = "sentiment_logs"

    log_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    feedback_id = Column(Integer, ForeignKey("feedback_items.feedback_id"), unique=True, nullable=False)
    label = Column(String(20), nullable=False)  # positive, neutral, negative
    score = Column(Float, nullable=False)       # -1.0 to +1.0
    confidence = Column(Float, nullable=False)  # max(p) 0.0 to 1.0
    p_pos = Column(Float, default=0.0)
    p_neu = Column(Float, default=0.0)
    p_neg = Column(Float, default=0.0)
    model_name = Column(String(100), default="transformer-hybrid-v1")
    processed_at = Column(DateTime, default=utc_now)

    feedback_item = relationship("FeedbackItem", back_populates="sentiment_log")

class Alert(Base):
    __tablename__ = "alerts"

    alert_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    source_id = Column(Integer, ForeignKey("sources.source_id"), nullable=True)
    alert_type = Column(String(50), nullable=False)  # sentiment_drop, critical_keyword, high_urgency
    severity = Column(String(20), default="medium")  # low, medium, high, critical
    message = Column(Text, nullable=False)
    channel = Column(String(30), default="in_app")  # in_app, email, slack
    status = Column(String(30), default="active")   # active, acknowledged, resolved
    triggered_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="alerts")
    source = relationship("Source", back_populates="alerts")
