from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Alert
from app.schemas import AlertResponse, AlertStatusUpdate

router = APIRouter(prefix="/api/alerts", tags=["Alert Engine & Notifications"])

@router.get("", response_model=list[AlertResponse])
def get_alerts(status: str | None = Query(None), db: Session = Depends(get_db)):
    """
    List alerts with optional status filter (active, acknowledged, resolved).
    """
    query = db.query(Alert)
    if status:
        query = query.filter(Alert.status == status)
    return query.order_by(Alert.triggered_at.desc()).all()

@router.patch("/{alert_id}/status")
def update_alert_status(alert_id: int, payload: AlertStatusUpdate, db: Session = Depends(get_db)):
    """
    Acknowledge or resolve an active alert.
    """
    alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = payload.status
    db.commit()
    return {"status": "success", "alert_id": alert.alert_id, "new_status": alert.status}

@router.post("/simulate")
def simulate_anomaly_alert(db: Session = Depends(get_db)):
    """
    Triggers a live demonstration anomaly alert for presentation and testing.
    """
    alert = Alert(
        user_id=1,
        source_id=1,
        alert_type="sentiment_drop",
        severity="critical",
        message="Simulated Alert: Google Play Store negative sentiment spiked to 68.4% (z-score: 2.89 > 2.50 threshold). Top recurring keywords: 'refund', 'crashes'.",
        channel="in_app",
        status="active",
        triggered_at=datetime.now(timezone.utc)
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return {"status": "success", "message": "Demo anomaly alert generated", "alert_id": alert.alert_id}
