import csv
import io
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.models import FeedbackItem, SentimentLog, Theme, Source, Alert
from app.nlp.preprocessor import clean_and_mask_text, compute_content_hash
from app.nlp.sentiment import analyze_sentiment
from app.nlp.theme_clusterer import theme_engine
from app.nlp.urgency import calculate_urgency
from app.services.alert_engine import check_and_generate_alerts

def get_or_create_theme(db: Session, label: str, keywords: str) -> Theme:
    theme = db.query(Theme).filter(Theme.label == label).first()
    if not theme:
        theme = Theme(label=label, keywords=keywords)
        db.add(theme)
        db.commit()
        db.refresh(theme)
    return theme

def process_single_feedback(
    db: Session,
    source_id: int,
    raw_text: str,
    rating: int | None = None,
    external_id: str | None = None,
    created_at: datetime | None = None
) -> tuple[FeedbackItem | None, bool]:
    """
    Executes the full NLP cascade:
    1. Normalisation & de-duplication
    2. PII masking
    3. Sentiment scoring
    4. Theme clustering
    5. Urgency scoring
    6. Database storage
    Returns: (FeedbackItem, is_duplicate)
    """
    if not raw_text or not raw_text.strip():
        return None, False

    # Check for duplicate
    content_hash = compute_content_hash(source_id, external_id, raw_text)
    existing = db.query(FeedbackItem).filter(
        FeedbackItem.source_id == source_id,
        FeedbackItem.external_id == content_hash
    ).first()

    if existing:
        return existing, True  # Duplicate item skipped

    # Pre-process & PII Masking
    cleaned_text, lang = clean_and_mask_text(raw_text)

    # Sentiment Classification
    sentiment_res = analyze_sentiment(cleaned_text, rating=rating)

    # Urgency scoring
    urgency_val, is_urgent, matched_kw = calculate_urgency(
        cleaned_text, sentiment_res.score, rating=rating
    )

    # Theme assignment
    theme_label, theme_keywords, sim = theme_engine.assign_theme(cleaned_text)
    theme = get_or_create_theme(db, theme_label, theme_keywords)

    item_created_at = created_at or datetime.now(timezone.utc)

    # Create FeedbackItem
    item = FeedbackItem(
        source_id=source_id,
        theme_id=theme.theme_id,
        external_id=content_hash,
        text=raw_text,
        cleaned_text=cleaned_text,
        rating=rating,
        language=lang,
        urgency_score=urgency_val,
        status="new",
        created_at=item_created_at,
        ingested_at=datetime.now(timezone.utc)
    )
    db.add(item)
    db.flush()

    # Create SentimentLog
    log = SentimentLog(
        feedback_id=item.feedback_id,
        label=sentiment_res.label,
        score=sentiment_res.score,
        confidence=sentiment_res.confidence,
        p_pos=sentiment_res.p_pos,
        p_neu=sentiment_res.p_neu,
        p_neg=sentiment_res.p_neg,
        model_name=sentiment_res.model_name,
        processed_at=datetime.now(timezone.utc)
    )
    db.add(log)
    db.commit()
    db.refresh(item)

    return item, False

def ingest_csv_content(db: Session, source_id: int, csv_text: str) -> dict:
    """
    Parses CSV text and processes each feedback row.
    Expected columns: text (required), rating, date/timestamp, id
    """
    reader = csv.DictReader(io.StringIO(csv_text))
    processed_count = 0
    duplicate_count = 0
    new_items = []

    for row in reader:
        # Resolve text column (case-insensitive search)
        text_key = next((k for k in row.keys() if k and k.lower() in ["text", "feedback", "review", "comment", "message"]), None)
        if not text_key or not row[text_key]:
            continue

        raw_text = row[text_key].strip()

        # Resolve rating
        rating_key = next((k for k in row.keys() if k and k.lower() in ["rating", "stars", "score"]), None)
        rating = None
        if rating_key and row[rating_key]:
            try:
                rating = int(float(row[rating_key]))
            except ValueError:
                pass

        # Resolve external ID
        id_key = next((k for k in row.keys() if k and k.lower() in ["id", "external_id", "review_id"]), None)
        ext_id = row[id_key] if id_key else None

        # Resolve Date
        date_key = next((k for k in row.keys() if k and k.lower() in ["date", "timestamp", "created_at"]), None)
        created_at = None
        if date_key and row[date_key]:
            try:
                # Try common formats
                raw_d = row[date_key].strip()
                for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%dT%H:%M:%SZ"]:
                    try:
                        created_at = datetime.strptime(raw_d, fmt).replace(tzinfo=timezone.utc)
                        break
                    except ValueError:
                        continue
            except Exception:
                created_at = None

        item, is_dup = process_single_feedback(db, source_id, raw_text, rating, ext_id, created_at)
        if is_dup:
            duplicate_count += 1
        elif item:
            processed_count += 1
            new_items.append(item)

    # Run alert detection on newly ingested items
    alerts = check_and_generate_alerts(db, new_items)

    # Update source last_synced_at
    source = db.query(Source).filter(Source.source_id == source_id).first()
    if source:
        source.last_synced_at = datetime.now(timezone.utc)
        db.commit()

    return {
        "processed": processed_count,
        "duplicates_skipped": duplicate_count,
        "alerts_triggered": len(alerts)
    }
