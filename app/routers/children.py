from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models.child import Child, ChildStatus
from app.models.vital import Vital
from app.models.alert import Alert

router = APIRouter(prefix="/children", tags=["Children"])

class ChildCreate(BaseModel):
    parent_id: str
    name: str
    age: int
    gender: str
    grade: Optional[str] = None
    school_name: Optional[str] = None
    school_start_time: Optional[str] = None
    school_end_time: Optional[str] = None

@router.get("/")
def get_children(parent_id: str, db: Session = Depends(get_db)):
    children = db.query(Child).filter(Child.parent_id == parent_id).all()
    result = []
    for child in children:
        latest = db.query(Vital).filter(
            Vital.child_id == child.id
        ).order_by(Vital.recorded_at.desc()).first()

        unresolved = db.query(Alert).filter(
            Alert.child_id == child.id,
            Alert.is_resolved == False
        ).count()

        result.append({
            "id": str(child.id),
            "name": child.name,
            "age": child.age,
            "gender": child.gender,
            "status": child.status,
            "unresolved_alerts": unresolved,
            "latest_vitals": latest,
            "band": child.band
        })
    return result

@router.post("/", status_code=201)
def create_child(data: ChildCreate, db: Session = Depends(get_db)):
    child = Child(**data.dict(), status=ChildStatus.SAFE)
    db.add(child)
    db.commit()
    db.refresh(child)
    return child

@router.get("/{child_id}")
def get_child(child_id: str, db: Session = Depends(get_db)):
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")
    return child

@router.delete("/{child_id}")
def delete_child(child_id: str, db: Session = Depends(get_db)):
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")
    db.delete(child)
    db.commit()
    return {"message": "Child removed"}

@router.get("/{child_id}/summary")
def get_child_summary(child_id: str, db: Session = Depends(get_db)):
    """
    Returns everything the app home screen needs
    in a single API call — vitals, alerts, location, band status
    """
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    # Latest vitals
    latest_vital = db.query(Vital).filter(
        Vital.child_id == child_id
    ).order_by(Vital.recorded_at.desc()).first()

    # Latest location
    from app.models.location import Location
    latest_location = db.query(Location).filter(
        Location.child_id == child_id
    ).order_by(Location.recorded_at.desc()).first()

    # Unresolved alerts count
    unresolved = db.query(Alert).filter(
        Alert.child_id == child_id,
        Alert.is_resolved == False
    ).count()

    # Last 3 alerts
    recent_alerts = db.query(Alert).filter(
        Alert.child_id == child_id
    ).order_by(Alert.created_at.desc()).limit(3).all()

    return {
        "child": {
            "id": str(child.id),
            "name": child.name,
            "age": child.age,
            "status": child.status,
        },
        "vitals": latest_vital,
        "location": latest_location,
        "band": child.band,
        "unresolved_alerts": unresolved,
        "recent_alerts": recent_alerts,
    }