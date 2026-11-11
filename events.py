"""API Router for Grouped Alert Events with Flood Prevention."""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.database import get_db
from app.models.entities import Event, AuditLog
from app.schemas.domain import EventSchema, EventActionRequest
from app.core.provenance import EventSeverity, ProvenanceType

router = APIRouter(prefix="/events", tags=["Event History & Alerts"])

@router.get("/", response_model=List[EventSchema])
def list_events(
    status_filter: Optional[str] = None,
    severity_filter: Optional[str] = None,
    parameter_filter: Optional[str] = None,
    equipment_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Returns grouped alert events with optional filtering.
    Notice: All events are non-binding engineering advisories.
    """
    query = db.query(Event)
    if status_filter:
        query = query.filter_by(status=status_filter.upper())
    if severity_filter:
        query = query.filter_by(severity=severity_filter.upper())
    if parameter_filter:
        query = query.filter_by(parameter=parameter_filter)
    if equipment_id:
        query = query.filter_by(equipment_id=equipment_id)
        
    return query.order_by(desc(Event.last_detected_at)).limit(100).all()

@router.post("/{event_uid}/action", response_model=EventSchema)
def act_on_event(event_uid: str, payload: EventActionRequest, db: Session = Depends(get_db)):
    """Acknowledge or resolve an active grouped alert event."""
    evt = db.query(Event).filter_by(event_uid=event_uid).first()
    if not evt:
        raise HTTPException(status_code=404, detail=f"Event '{event_uid}' not found")
        
    action_upper = payload.action.upper()
    now = datetime.now(timezone.utc)
    
    if action_upper == "ACKNOWLEDGE":
        evt.status = "ACKNOWLEDGED"
        evt.acknowledged_by = payload.user_id
    elif action_upper == "RESOLVE":
        evt.status = "RESOLVED"
        evt.resolved_at = now
    else:
        raise HTTPException(status_code=400, detail="Action must be 'ACKNOWLEDGE' or 'RESOLVE'")
        
    audit = AuditLog(
        user_id=payload.user_id,
        role="OPERATOR",
        action=f"{action_upper}_ALERT_EVENT",
        entity="EVENT",
        entity_id=event_uid,
        details={"status": evt.status},
        provenance=ProvenanceType.DERIVED
    )
    db.add(audit)
    db.commit()
    db.refresh(evt)
    return evt
