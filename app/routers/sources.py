import random
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Source, FeedbackItem
from app.schemas import SourceCreate, SourceResponse
from app.services.ingestion import process_single_feedback
from app.services.alert_engine import check_and_generate_alerts

router = APIRouter(prefix="/api/sources", tags=["Feedback Sources"])

SAMPLE_SYNC_FEEDBACK = [
    ("The latest app update fixes the battery drain and feels super fast!", 5),
    ("Charged twice for my monthly subscription and support ticket is ignored. Total scam!", 1),
    ("Delivery was delayed by 4 days, but the packaging and product quality are decent.", 3),
    ("Customer support agent was very polite and solved my invoice query in 2 minutes.", 5),
    ("App crashes every time I click on checkout. Please fix this bug immediately!", 1),
    ("Decent value for money. Would appreciate if dark mode is added in future updates.", 4),
    ("Completely broken payment gateway. Need a refund immediately or I will cancel my account.", 1),
    ("Very pleasant experience visiting the store. Staff was friendly and accommodating.", 5)
]

@router.get("", response_model=list[SourceResponse])
def get_sources(db: Session = Depends(get_db)):
    """
    List all configured customer feedback sources.
    """
    return db.query(Source).all()

@router.post("", response_model=SourceResponse)
def create_source(source_in: SourceCreate, db: Session = Depends(get_db)):
    """
    Add a new feedback channel (Owner or Admin).
    """
    source = Source(
        user_id=source_in.user_id,
        name=source_in.name,
        source_type=source_in.source_type,
        api_config=source_in.api_config or "{}",
        status="active"
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source

@router.post("/{source_id}/sync-demo")
def sync_demo_reviews(source_id: int, count: int = 5, db: Session = Depends(get_db)):
    """
    Simulates real-time polling/sync from external APIs (Google Play, Google Reviews, Helpdesk).
    """
    source = db.query(Source).filter(Source.source_id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    new_items = []
    selected_samples = random.sample(SAMPLE_SYNC_FEEDBACK, min(count, len(SAMPLE_SYNC_FEEDBACK)))

    for text, rating in selected_samples:
        # Add random salt to text for demo variation
        variation_text = text + f" (Ref: #{random.randint(1000, 9999)})"
        item, is_dup = process_single_feedback(
            db=db,
            source_id=source_id,
            raw_text=variation_text,
            rating=rating,
            created_at=datetime.now(timezone.utc) - timedelta(minutes=random.randint(5, 120))
        )
        if item and not is_dup:
            new_items.append(item)

    # Check alerts
    alerts = check_and_generate_alerts(db, new_items)

    source.last_synced_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "status": "success",
        "synced_count": len(new_items),
        "alerts_triggered": len(alerts),
        "source": source.name
    }
