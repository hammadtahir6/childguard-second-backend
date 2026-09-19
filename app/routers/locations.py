from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database import get_db
from app.models.location import Location

router = APIRouter(prefix="/locations", tags=["Locations"])

@router.get("/{child_id}/history")
def get_location_history(
    child_id: str,
    hours: int = 24,
    db: Session = Depends(get_db)
):
    since = datetime.utcnow() - timedelta(hours=hours)
    locations = db.query(Location).filter(
        Location.child_id == child_id,
        Location.recorded_at >= since
    ).order_by(Location.recorded_at.asc()).all()
    return locations

@router.get("/{child_id}/current")
def get_current_location(child_id: str, db: Session = Depends(get_db)):
    location = db.query(Location).filter(
        Location.child_id == child_id
    ).order_by(Location.recorded_at.desc()).first()
    return location