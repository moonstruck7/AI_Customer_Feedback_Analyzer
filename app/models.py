from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.database import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="SMB Owner")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    sources: Mapped[List["Source"]] = relationship("Source", back_populates="owner", cascade="all, delete-orphan")
    alerts: Mapped[List["Alert"]] = relationship("Alert", back_populates="user", cascade="all, delete-orphan")

class Source(Base):
    __tablename__ = "sources"

    source_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id"), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    api_config: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[str] = mapped_column(String(30), default="active")
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    owner: Mapped["User"] = relationship("User", back_populates="sources")
    feedback_items: Mapped[List["FeedbackItem"]] = relationship("FeedbackItem", back_populates="source", cascade="all, delete-orphan")
    alerts: Mapped[List["Alert"]] = relationship("Alert", back_populates="source", cascade="all, delete-orphan")

class Theme(Base):
    __tablename__ = "themes"

    theme_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    label: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    keywords: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    feedback_items: Mapped[List["FeedbackItem"]] = relationship("FeedbackItem", back_populates="theme")

class FeedbackItem(Base):
    __tablename__ = "feedback_items"

    feedback_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(Integer, ForeignKey("sources.source_id"), nullable=False)
    theme_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("themes.theme_id"), nullable=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(128), index=True, nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    cleaned_text: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    language: Mapped[str] = mapped_column(String(20), default="en")
    urgency_score: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(30), default="new")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    ingested_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    source: Mapped["Source"] = relationship("Source", back_populates="feedback_items")
    theme: Mapped[Optional["Theme"]] = relationship("Theme", back_populates="feedback_items")
    sentiment_log: Mapped[Optional["SentimentLog"]] = relationship("SentimentLog", back_populates="feedback_item", uselist=False, cascade="all, delete-orphan")

class SentimentLog(Base):
    __tablename__ = "sentiment_logs"

    log_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    feedback_id: Mapped[int] = mapped_column(Integer, ForeignKey("feedback_items.feedback_id"), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(20), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    p_pos: Mapped[float] = mapped_column(Float, default=0.0)
    p_neu: Mapped[float] = mapped_column(Float, default=0.0)
    p_neg: Mapped[float] = mapped_column(Float, default=0.0)
    model_name: Mapped[str] = mapped_column(String(100), default="transformer-hybrid-v1")
    processed_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    feedback_item: Mapped["FeedbackItem"] = relationship("FeedbackItem", back_populates="sentiment_log")

class Alert(Base):
    __tablename__ = "alerts"

    alert_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id"), nullable=False)
    source_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("sources.source_id"), nullable=True)
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="medium")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[str] = mapped_column(String(30), default="in_app")
    status: Mapped[str] = mapped_column(String(30), default="active")
    triggered_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    user: Mapped["User"] = relationship("User", back_populates="alerts")
    source: Mapped[Optional["Source"]] = relationship("Source", back_populates="alerts")
