"""API Router for Electrical Telemetry."""
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.database import get_db
from app.models.entities import Telemetry, Equipment
from app.schemas.domain import TelemetrySchema

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])

@router.get("/latest", response_model=List[TelemetrySchema])
def get_latest_telemetry_all(db: Session = Depends(get_db)):
    """Returns the most recent telemetry sample for every equipment item."""
    equipment_ids = [eq.id for eq in db.query(Equipment.id).all()]
    latest_samples = []
    
    for eq_id in equipment_ids:
        latest = (
            db.query(Telemetry)
            .filter_by(equipment_id=eq_id)
            .order_by(desc(Telemetry.timestamp))
            .first()
        )
        if latest:
            latest_samples.append(latest)
            
    return latest_samples

@router.get("/history", response_model=List[TelemetrySchema])
def get_telemetry_history(
    equipment_id: Optional[str] = None,
    limit: int = Query(120, le=1000),
    db: Session = Depends(get_db)
):
    """Returns timestamped telemetry history, optionally filtered by equipment."""
    query = db.query(Telemetry)
    if equipment_id:
        query = query.filter_by(equipment_id=equipment_id)
    return query.order_by(desc(Telemetry.timestamp)).limit(limit).all()[::-1]
