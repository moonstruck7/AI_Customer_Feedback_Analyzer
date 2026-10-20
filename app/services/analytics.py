from datetime import datetime, timedelta, timezone
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models import FeedbackItem, SentimentLog, Theme, Source, Alert

def get_dashboard_metrics(db: Session, source_id: int | None = None, days: int = 30) -> dict:
    """
    Computes summary metrics:
    - Net Sentiment Score (NSS = ((Positive - Negative) / Total) * 100)
    - Total Volume, Positive/Neutral/Negative counts & percentages
    - Average Rating
    - High Urgency Complaints count
    - Active Alerts count
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    query = db.query(FeedbackItem).join(SentimentLog).filter(FeedbackItem.ingested_at >= cutoff)
    if source_id:
        query = query.filter(FeedbackItem.source_id == source_id)

    total_count = query.count()

    if total_count == 0:
        return {
            "total_feedback": 0,
            "positive_count": 0,
            "neutral_count": 0,
            "negative_count": 0,
            "positive_pct": 0.0,
            "neutral_pct": 0.0,
            "negative_pct": 0.0,
            "net_sentiment_score": 0.0,
            "avg_rating": 0.0,
            "urgent_complaints_count": 0,
            "active_alerts_count": db.query(Alert).filter(Alert.status == "active").count()
        }

    pos_count = query.filter(SentimentLog.label == "positive").count()
    neu_count = query.filter(SentimentLog.label == "neutral").count()
    neg_count = query.filter(SentimentLog.label == "negative").count()

    # Net Sentiment Score calculation (Section 7.1)
    nss = round(((pos_count - neg_count) / total_count) * 100, 1)

    # Average rating (only from items that have a rating)
    rating_items = query.filter(FeedbackItem.rating.isnot(None)).all()
    avg_rating = round(sum(it.rating for it in rating_items) / len(rating_items), 2) if rating_items else 0.0

    # Urgent complaints (urgency_score >= 60.0)
    urgent_count = query.filter(FeedbackItem.urgency_score >= 60.0, FeedbackItem.status != "resolved").count()
    active_alerts = db.query(Alert).filter(Alert.status == "active").count()

    return {
        "total_feedback": total_count,
        "positive_count": pos_count,
        "neutral_count": neu_count,
        "negative_count": neg_count,
        "positive_pct": round((pos_count / total_count) * 100, 1),
        "neutral_pct": round((neu_count / total_count) * 100, 1),
        "negative_pct": round((neg_count / total_count) * 100, 1),
        "net_sentiment_score": nss,
        "avg_rating": avg_rating,
        "urgent_complaints_count": urgent_count,
        "active_alerts_count": active_alerts
    }

def get_sentiment_trends(db: Session, source_id: int | None = None, days: int = 14) -> list[dict]:
    """
    Returns daily trend data: date, positive, neutral, negative counts, and daily NSS.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    query = db.query(FeedbackItem, SentimentLog).join(SentimentLog, FeedbackItem.feedback_id == SentimentLog.feedback_id).filter(FeedbackItem.created_at >= cutoff)
    if source_id:
        query = query.filter(FeedbackItem.source_id == source_id)

    items = query.all()

    # Bucket by date (YYYY-MM-DD)
    date_buckets = {}
    for i in range(days + 1):
        d_str = (cutoff + timedelta(days=i)).strftime("%Y-%m-%d")
        date_buckets[d_str] = {"positive": 0, "neutral": 0, "negative": 0}

    for item, log in items:
        d_str = item.created_at.strftime("%Y-%m-%d")
        if d_str in date_buckets:
            lbl = log.label.lower()
            if lbl in date_buckets[d_str]:
                date_buckets[d_str][lbl] += 1

    trend_list = []
    for d_str, counts in sorted(date_buckets.items()):
        total = counts["positive"] + counts["neutral"] + counts["negative"]
        nss = round(((counts["positive"] - counts["negative"]) / total) * 100, 1) if total > 0 else 0.0
        trend_list.append({
            "date": d_str,
            "positive": counts["positive"],
            "neutral": counts["neutral"],
            "negative": counts["negative"],
            "total": total,
            "nss": nss
        })

    return trend_list

def get_channel_distribution(db: Session) -> list[dict]:
    """
    Returns feedback volume and average sentiment score grouped by Source/Channel.
    """
    results = db.query(
        Source.source_type,
        Source.name,
        func.count(FeedbackItem.feedback_id).label("count"),
        func.avg(SentimentLog.score).label("avg_sentiment")
    ).join(FeedbackItem, Source.source_id == FeedbackItem.source_id)\
     .join(SentimentLog, FeedbackItem.feedback_id == SentimentLog.feedback_id)\
     .group_by(Source.source_type, Source.name).all()

    channels = []
    for stype, sname, count, avg_sent in results:
        channels.append({
            "source_type": stype,
            "name": sname,
            "count": count,
            "avg_sentiment": round(float(avg_sent), 3) if avg_sent is not None else 0.0
        })
    return channels

def get_theme_analytics(db: Session) -> list[dict]:
    """
    Returns breakdown for all themes: feedback count, sentiment breakdown, and keywords.
    """
    themes = db.query(Theme).all()
    analytics = []

    for th in themes:
        items = db.query(FeedbackItem, SentimentLog).join(SentimentLog).filter(FeedbackItem.theme_id == th.theme_id).all()
        count = len(items)
        if count == 0:
            continue

        pos = sum(1 for it, log in items if log.label == "positive")
        neu = sum(1 for it, log in items if log.label == "neutral")
        neg = sum(1 for it, log in items if log.label == "negative")
        avg_score = sum(log.score for it, log in items) / count

        analytics.append({
            "theme_id": th.theme_id,
            "label": th.label,
            "keywords": th.keywords,
            "total_count": count,
            "positive": pos,
            "neutral": neu,
            "negative": neg,
            "avg_score": round(avg_score, 3)
        })

    # Sort descending by total items
    analytics.sort(key=lambda x: x["total_count"], reverse=True)
    return analytics
