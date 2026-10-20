import io
import csv
from fastapi import APIRouter, Depends, Response, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import FeedbackItem
from app.services.analytics import (
    get_dashboard_metrics,
    get_sentiment_trends,
    get_channel_distribution,
    get_theme_analytics
)

router = APIRouter(prefix="/api/analytics", tags=["Analytics & Reporting"])

@router.get("/metrics")
def metrics_endpoint(source_id: int | None = Query(None), days: int = Query(30), db: Session = Depends(get_db)):
    """
    Returns Net Sentiment Score (NSS) and key summary KPI metrics.
    """
    return get_dashboard_metrics(db, source_id=source_id, days=days)

@router.get("/trends")
def trends_endpoint(source_id: int | None = Query(None), days: int = Query(14), db: Session = Depends(get_db)):
    """
    Returns daily sentiment distribution and daily NSS over time.
    """
    return get_sentiment_trends(db, source_id=source_id, days=days)

@router.get("/channels")
def channels_endpoint(db: Session = Depends(get_db)):
    """
    Returns volume and average sentiment score grouped by channel/source.
    """
    return get_channel_distribution(db)

@router.get("/themes")
def themes_endpoint(db: Session = Depends(get_db)):
    """
    Returns topic clusters with keyword frequencies and sentiment breakdown.
    """
    return get_theme_analytics(db)

@router.get("/export-csv")
def export_feedback_csv(source_id: int | None = Query(None), db: Session = Depends(get_db)):
    """
    Exports all analyzed feedback records with sentiment, scores, and themes as CSV.
    """
    query = db.query(FeedbackItem)
    if source_id:
        query = query.filter(FeedbackItem.source_id == source_id)
    items = query.order_by(FeedbackItem.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Feedback ID", "Source", "Date", "Original Text", "Cleaned Text",
        "Rating", "Language", "Sentiment Label", "Intensity Score (-1 to 1)",
        "Confidence", "Theme", "Urgency Score", "Status"
    ])

    for it in items:
        writer.writerow([
            it.feedback_id,
            it.source.name if it.source else "N/A",
            it.created_at.strftime("%Y-%m-%d %H:%M:%S") if it.created_at else "",
            it.text,
            it.cleaned_text,
            it.rating or "",
            it.language,
            it.sentiment_log.label if it.sentiment_log else "N/A",
            it.sentiment_log.score if it.sentiment_log else "",
            it.sentiment_log.confidence if it.sentiment_log else "",
            it.theme.label if it.theme else "General Feedback",
            it.urgency_score,
            it.status
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=customer_feedback_analysis.csv"}
    )
