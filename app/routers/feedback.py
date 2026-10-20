from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import FeedbackItem, Source
from app.schemas import FeedbackCreate, FeedbackItemResponse, FeedbackStatusUpdate
from app.services.ingestion import process_single_feedback, ingest_csv_content
from app.services.alert_engine import check_and_generate_alerts

router = APIRouter(prefix="/api/feedback", tags=["Feedback Ingestion & Management"])

@router.post("/single")
def ingest_single(item_in: FeedbackCreate, db: Session = Depends(get_db)):
    """
    Ingest a single feedback text in real-time. Runs the complete NLP pipeline and returns the scored item.
    """
    source = db.query(Source).filter(Source.source_id == item_in.source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    item, is_dup = process_single_feedback(
        db=db,
        source_id=item_in.source_id,
        raw_text=item_in.text,
        rating=item_in.rating,
        external_id=item_in.external_id
    )

    if is_dup:
        return {"status": "skipped", "message": "Duplicate feedback detected and discarded.", "feedback_id": item.feedback_id}

    # Run alert check
    alerts = check_and_generate_alerts(db, [item])

    return {
        "status": "success",
        "feedback_id": item.feedback_id,
        "sentiment": item.sentiment_log.label,
        "sentiment_score": item.sentiment_log.score,
        "confidence": item.sentiment_log.confidence,
        "theme": item.theme.label if item.theme else "General Feedback",
        "urgency_score": item.urgency_score,
        "cleaned_text": item.cleaned_text,
        "alerts_triggered": len(alerts)
    }

@router.post("/upload-csv")
async def upload_csv(
    file: UploadFile = File(...),
    source_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """
    Upload a bulk CSV file containing feedback items. Automatically parses text, ratings, and timestamps.
    """
    source = db.query(Source).filter(Source.source_id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Target source ID not found")

    content = await file.read()
    try:
        csv_text = content.decode("utf-8")
    except UnicodeDecodeError:
        csv_text = content.decode("latin-1")

    stats = ingest_csv_content(db, source_id, csv_text)
    return {
        "status": "success",
        "filename": file.filename,
        "source": source.name,
        **stats
    }

@router.get("", response_model=list[FeedbackItemResponse])
def list_feedback(
    source_id: int | None = Query(None),
    theme_id: int | None = Query(None),
    sentiment: str | None = Query(None),
    urgent_only: bool = Query(False),
    status: str | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    """
    Query customer feedback with rich filters (sentiment, urgency, source, theme, status).
    """
    query = db.query(FeedbackItem)

    if source_id:
        query = query.filter(FeedbackItem.source_id == source_id)
    if theme_id:
        query = query.filter(FeedbackItem.theme_id == theme_id)
    if sentiment:
        from app.models import SentimentLog
        query = query.join(SentimentLog).filter(SentimentLog.label == sentiment.lower())
    if urgent_only:
        query = query.filter(FeedbackItem.urgency_score >= 60.0)
    if status:
        query = query.filter(FeedbackItem.status == status)

    # Sort urgent items first, then by date descending
    items = query.order_by(FeedbackItem.urgency_score.desc(), FeedbackItem.created_at.desc()).offset(offset).limit(limit).all()

    # Enrich with source_name
    for it in items:
        it.source_name = it.source.name if it.source else "Unknown"

    return items

@router.patch("/{feedback_id}/status")
def update_feedback_status(feedback_id: int, payload: FeedbackStatusUpdate, db: Session = Depends(get_db)):
    """
    Update complaint resolution status (Support Manager capability).
    """
    item = db.query(FeedbackItem).filter(FeedbackItem.feedback_id == feedback_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Feedback item not found")

    item.status = payload.status
    db.commit()
    return {"status": "success", "feedback_id": item.feedback_id, "new_status": item.status}
