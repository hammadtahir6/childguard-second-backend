from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.band import Band
from app.models.child import Child

router = APIRouter(prefix="/bands", tags=["Bands"])

class PairBandRequest(BaseModel):
    band_code: str
    child_id: str

@router.post("/pair")
def pair_band(data: PairBandRequest, db: Session = Depends(get_db)):
    # Check band exists or create it
    band = db.query(Band).filter(Band.band_code == data.band_code).first()
    if not band:
        band = Band(band_code=data.band_code, is_paired=False)
        db.add(band)
        db.commit()
        db.refresh(band)

    if band.is_paired and str(band.child_id) != data.child_id:
        raise HTTPException(status_code=400, detail="Band already paired to another child")

    # Pair band to child
    band.child_id = data.child_id
    band.is_paired = True
    db.commit()

    return {"message": "Band paired successfully", "band_code": data.band_code}

@router.get("/check/{band_code}")
def check_band(band_code: str, db: Session = Depends(get_db)):
    band = db.query(Band).filter(Band.band_code == band_code).first()
    if not band:
        return {"exists": False, "paired": False}
    return {
        "exists": True,
        "paired": band.is_paired,
        "child_id": str(band.child_id) if band.child_id else None
    }

@router.post("/unpair/{band_code}")
def unpair_band(band_code: str, db: Session = Depends(get_db)):
    band = db.query(Band).filter(Band.band_code == band_code).first()
    if not band:
        raise HTTPException(status_code=404, detail="Band not found")
    band.child_id = None
    band.is_paired = False
    band.is_connected = False
    db.commit()
    return {"message": "Band unpaired successfully"}