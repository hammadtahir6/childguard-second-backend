from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import uuid
from app.database import get_db
from app.models.alert import Alert, AlertSeverity
from app.models.child import Child

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("/")
def get_alerts(
    child_id: Optional[str] = None,
    severity: Optional[str] = None,
    resolved: Optional[bool] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(Alert)
    
    if child_id:
        try:
            parsed_child_id = uuid.UUID(child_id)
            query = query.filter(Alert.child_id == parsed_child_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid child_id UUID format")
            
    if severity:
        try:
            severity_enum = AlertSeverity[severity.upper()]
            query = query.filter(Alert.severity == severity_enum)
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid severity type: {severity}")
            
    if resolved is not None:
        query = query.filter(Alert.is_resolved == resolved)
        
    return query.order_by(Alert.created_at.desc()).limit(limit).all()

@router.get("/unresolved-count")
def get_unresolved_count(db: Session = Depends(get_db)):
    count = db.query(Alert).filter(Alert.is_resolved == False).count()
    return {"unresolved_count": count}

@router.patch("/{alert_id}/resolve")
def resolve_alert(alert_id: str, db: Session = Depends(get_db)):
    try:
        parsed_alert_id = uuid.UUID(alert_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid alert_id UUID format")

    alert = db.query(Alert).filter(Alert.id == parsed_alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    alert.is_resolved = True
    alert.resolved_at = datetime.utcnow()
    db.commit()
    return {"message": "Alert resolved"}

import enum

class AlertType(str, enum.Enum):
    FALL_DETECTED = "FALL_DETECTED"
    PANIC_PRESSED = "PANIC_PRESSED"
    ANOMALY_DETECTED = "ANOMALY_DETECTED"
    BEHAVIOR_ABNORMAL = "BEHAVIOR_ABNORMAL"
    SOUND_ALERT = "SOUND_ALERT"
    SCREAMING_DETECTED = "SCREAMING_DETECTED"
    UNKNOWN = "UNKNOWN"  # A safe catch-all