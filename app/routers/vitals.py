from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.models.vital import Vital
from app.models.alert import Alert, AlertType, AlertSeverity
from app.models.child import Child, ChildStatus
from app.models.location import Location
from app.models.band import Band
from app.services.ai_service import run_all_models

router = APIRouter(prefix="/vitals", tags=["Vitals"])

class VitalCreate(BaseModel):
    child_id: str
    heart_rate: Optional[float] = None
    spo2: Optional[float] = None
    temperature: Optional[float] = None
    accel_x: Optional[float] = None
    accel_y: Optional[float] = None
    accel_z: Optional[float] = None
    gyro_x: Optional[float] = None
    gyro_y: Optional[float] = None
    gyro_z: Optional[float] = None
    sound_level: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    fall_detected: bool = False
    panic_pressed: bool = False
    band_on_wrist: bool = True
    battery_percent: Optional[float] = None

@router.post("/")
def receive_vitals(data: VitalCreate, db: Session = Depends(get_db)):
    """
    Main endpoint — ESP32 sends data here every 5 seconds
    Runs all 4 AI models and creates alerts if needed
    """
    # Verify child exists
    child = db.query(Child).filter(Child.id == data.child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    # Run all AI models
    vital_dict = data.dict()
    ai_results = run_all_models(vital_dict, data.child_id)

    # Save vitals to database
    vital = Vital(
        child_id=data.child_id,
        heart_rate=data.heart_rate,
        spo2=data.spo2,
        temperature=data.temperature,
        accel_x=data.accel_x,
        accel_y=data.accel_y,
        accel_z=data.accel_z,
        gyro_x=data.gyro_x,
        gyro_y=data.gyro_y,
        gyro_z=data.gyro_z,
        sound_level=data.sound_level,
        latitude=data.latitude,
        longitude=data.longitude,
        fall_detected=ai_results["fall_detected"],
        anomaly_detected=ai_results["anomaly_detected"],
        behavior_abnormal=ai_results["behavior_abnormal"],
        sound_alert=ai_results["sound_alert"],
        sound_type=ai_results["sound_type"],
        panic_pressed=data.panic_pressed,
        band_on_wrist=data.band_on_wrist,
        battery_percent=data.battery_percent,
    )
    db.add(vital)

    # Save location
    if data.latitude and data.longitude:
        location = Location(
            child_id=data.child_id,
            latitude=data.latitude,
            longitude=data.longitude,
        )
        db.add(location)

    # Update band status
    band = db.query(Band).filter(Band.child_id == data.child_id).first()
    if band:
        band.is_connected = True
        band.last_seen = datetime.utcnow()
        if data.battery_percent:
            band.battery_level = int(data.battery_percent)

    # Create alerts from AI results
    # Create alerts from AI results
    has_emergency = False
    for alert_data in ai_results["alerts_to_create"]:
        raw_type = alert_data.get("type", "SOUND_ALERT")
        
        # Safely map string to Enum, fallback if unknown
# Safely map string to Enum, fallback to the first available member if unknown
        try:
            alert_type_enum = AlertType[raw_type]
        except KeyError:
            # Fallback to the first member available in AlertType safely
            alert_type_enum = list(AlertType)[0]

        alert = Alert(
            child_id=data.child_id,
            alert_type=alert_type_enum,
            severity=AlertSeverity[alert_data.get("severity", "WARNING")],
            title=alert_data.get("title", "Alert"),
            description=alert_data.get("description", ""),
            latitude=data.latitude,
            longitude=data.longitude,
            heart_rate_at_alert=data.heart_rate,
            spo2_at_alert=data.spo2,
            temperature_at_alert=data.temperature,
        )
        db.add(alert)
        if alert_data.get("severity") == "EMERGENCY":
            has_emergency = True

    # Update child status
    if has_emergency:
        child.status = ChildStatus.EMERGENCY
    elif ai_results["anomaly_detected"] or ai_results["behavior_abnormal"]:
        child.status = ChildStatus.WARNING
    else:
        child.status = ChildStatus.SAFE

    db.commit()

    return {
        "status": "received",
        "ai_results": ai_results,
        "child_status": child.status,
        "alerts_created": len(ai_results["alerts_to_create"])
    }

@router.get("/{child_id}/latest")
def get_latest_vitals(child_id: str, db: Session = Depends(get_db)):
    vital = db.query(Vital).filter(
        Vital.child_id == child_id
    ).order_by(Vital.recorded_at.desc()).first()

    if not vital:
        raise HTTPException(status_code=404, detail="No vitals found")

    return vital

@router.get("/{child_id}/history")
def get_vitals_history(
    child_id: str,
    hours: int = 24,
    db: Session = Depends(get_db)
):
    from datetime import timedelta
    since = datetime.utcnow() - timedelta(hours=hours)
    vitals = db.query(Vital).filter(
        Vital.child_id == child_id,
        Vital.recorded_at >= since
    ).order_by(Vital.recorded_at.asc()).all()
    return vitals