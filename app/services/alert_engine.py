import math
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.models import Alert, FeedbackItem, SentimentLog, Source, User
from app.config import settings

def check_and_generate_alerts(db: Session, newly_processed_items: list[FeedbackItem]) -> list[Alert]:
    """
    Implements Step 11:
    1. Evaluates individual high-urgency / critical keyword triggers.
    2. Runs statistical anomaly detection on rolling baseline negative feedback share:
       z = (p - mu) / sigma > 2.5
    3. Respects alert cooldowns to avoid notification fatigue.
    """
    generated_alerts = []
    now = datetime.now(timezone.utc)

    # 1. Immediate Critical Feedback Items
    for item in newly_processed_items:
        if item.urgency_score >= 70.0:
            # Check cooldown for similar alert in last 2 hours
            recent_alert = db.query(Alert).filter(
                Alert.source_id == item.source_id,
                Alert.alert_type == "high_urgency",
                Alert.triggered_at >= now - timedelta(hours=2)
            ).first()

            if not recent_alert:
                source = db.query(Source).filter(Source.source_id == item.source_id).first()
                source_name = source.name if source else "Unknown Source"
                user_id = source.user_id if source else 1

                alert = Alert(
                    user_id=user_id,
                    source_id=item.source_id,
                    alert_type="high_urgency",
                    severity="critical" if item.urgency_score >= 85 else "high",
                    message=f"Critical customer complaint detected in {source_name} (Urgency: {item.urgency_score}%): '{item.cleaned_text[:120]}...'",
                    channel="in_app",
                    status="active",
                    triggered_at=now
                )
                db.add(alert)
                generated_alerts.append(alert)

    # 2. Statistical Anomaly Detection (Section 7.1 Step 11)
    # Group items by source to calculate negative share p vs baseline mu, sigma
    source_ids = list(set([item.source_id for item in newly_processed_items]))
    for sid in source_ids:
        # Check cooldown for anomaly alert
        recent_anomaly = db.query(Alert).filter(
            Alert.source_id == sid,
            Alert.alert_type == "sentiment_drop",
            Alert.triggered_at >= now - timedelta(hours=6)
        ).first()
        if recent_anomaly:
            continue

        # Look at last 24 hours of feedback for this source
        last_24h_items = db.query(FeedbackItem).join(SentimentLog).filter(
            FeedbackItem.source_id == sid,
            FeedbackItem.ingested_at >= now - timedelta(days=1)
        ).all()

        total_24h = len(last_24h_items)
        if total_24h < settings.MIN_DAILY_FEEDBACK_VOLUME:
            continue

        neg_24h = sum(1 for it in last_24h_items if it.sentiment_log and it.sentiment_log.label == "negative")
        p_current = neg_24h / total_24h  # Negative share in last 24h

        # Compute historical baseline (past 28 days)
        baseline_start = now - timedelta(days=settings.ROLLING_BASELINE_DAYS)
        historical_items = db.query(FeedbackItem).join(SentimentLog).filter(
            FeedbackItem.source_id == sid,
            FeedbackItem.ingested_at >= baseline_start,
            FeedbackItem.ingested_at < now - timedelta(days=1)
        ).all()

        if len(historical_items) >= 15:
            # Calculate daily historical negative shares
            daily_shares = []
            for day_offset in range(1, settings.ROLLING_BASELINE_DAYS):
                d_start = now - timedelta(days=day_offset + 1)
                d_end = now - timedelta(days=day_offset)
                day_items = [it for it in historical_items if d_start <= it.ingested_at < d_end]
                if len(day_items) >= 3:
                    day_neg = sum(1 for it in day_items if it.sentiment_log and it.sentiment_log.label == "negative")
                    daily_shares.append(day_neg / len(day_items))

            if len(daily_shares) >= 5:
                mu = sum(daily_shares) / len(daily_shares)
                variance = sum((x - mu) ** 2 for x in daily_shares) / len(daily_shares)
                sigma = math.sqrt(variance)

                if sigma > 0.01:
                    z = (p_current - mu) / sigma
                    if z > settings.ANOMALY_Z_SCORE_THRESHOLD:
                        source = db.query(Source).filter(Source.source_id == sid).first()
                        source_name = source.name if source else f"Source #{sid}"
                        user_id = source.user_id if source else 1

                        alert = Alert(
                            user_id=user_id,
                            source_id=sid,
                            alert_type="sentiment_drop",
                            severity="critical" if z > 3.2 else "high",
                            message=f"Statistical anomaly in {source_name}: Negative sentiment spiked to {round(p_current*100, 1)}% (z-score: {round(z, 2)} > {settings.ANOMALY_Z_SCORE_THRESHOLD}). Rolling mean: {round(mu*100, 1)}%.",
                            channel="in_app",
                            status="active",
                            triggered_at=now
                        )
                        db.add(alert)
                        generated_alerts.append(alert)

    if generated_alerts:
        db.commit()
        for a in generated_alerts:
            db.refresh(a)

    return generated_alerts
