"""API Router for 8-Step Logical Flow Decisions and Recommendations."""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.database import get_db
from app.models.entities import Decision, Equipment, SiteConfig
from app.schemas.domain import DecisionSchema
from app.core.provenance import ProvenanceType

router = APIRouter(prefix="/decisions", tags=["Decisions & Optimisation"])

@router.get("/latest", response_model=List[DecisionSchema])
def get_latest_decisions_all(db: Session = Depends(get_db)):
    """Returns the most recent decision and 8-step decision trace for every equipment item."""
    equipment_ids = [eq.id for eq in db.query(Equipment.id).all()]
    results = []
    
    for eq_id in equipment_ids:
        latest = (
            db.query(Decision)
            .filter_by(equipment_id=eq_id)
            .order_by(desc(Decision.timestamp))
            .first()
        )
        if latest:
            results.append(latest)
            
    return results

@router.get("/equipment/{equipment_id}", response_model=DecisionSchema)
def get_decision_for_equipment(equipment_id: str, db: Session = Depends(get_db)):
    latest = (
        db.query(Decision)
        .filter_by(equipment_id=equipment_id)
        .order_by(desc(Decision.timestamp))
        .first()
    )
    if not latest:
        raise HTTPException(status_code=404, detail="No decision record found for equipment")
    return latest

@router.get("/tradeoffs")
def get_tradeoff_checklist():
    """Answers the track question: 'What trade-offs should be checked?'
    Comprehensive checklist covering electrical, mechanical, and process considerations.
    """
    return {
        "title": "What trade-offs should be checked?",
        "subtitle": "Engineering impact assessment of controlled idle shutdown",
        "tradeoffs": [
            {
                "category": "Electrical & Thermal Stress",
                "risk": "Motor Inrush Current & Winding Thermal Cycling",
                "detail": "Direct-on-line (DOL) motor starting pulls 6-8x rated current, heating stator windings. Repeated start-stops accelerate insulation aging.",
                "mitigation": "Enforce strict max restarts per hour (default max 4/hr), minimum off-time cooldown (180s), and soft-starter/VFD ramp profiles.",
                "status_check": "Restart rate limiter active"
            },
            {
                "category": "Process Operability",
                "risk": "Auxiliary Restart Delay & Line Resumption Lag",
                "detail": "Shutting down pneumatic compressors or exhaust fans requires spin-up and pressurization delay before upstream production can restart.",
                "mitigation": "Configurable t_delay buffer (120-240s) ensures equipment only shuts down during verified extended shift pauses, with pre-restart audio/visual beacons.",
                "status_check": "Delay thresholds verified"
            },
            {
                "category": "Safety & Critical Service",
                "risk": "Unintended Shutdown of Critical Safety/Cooling Loads",
                "detail": "De-energizing cooling water pumps or fume extraction can cause thermal runaway or regulatory air-quality breach.",
                "mitigation": "HARDWARE & SOFTWARE PERMANENT EXCLUSION: Critical equipment cannot be assigned to automated shutdown under any configuration.",
                "status_check": "Critical loads permanently locked"
            },
            {
                "category": "Mechanical Wear",
                "risk": "Belt, Coupling, and Valve Cycle Fatigue",
                "detail": "Frequent stopping of conveyor belts and pump check valves increases mechanical cyclic stress.",
                "mitigation": "Prioritize high-idle duration assets (>15 mins) over short cycling; use VFD controlled deceleration where equipped.",
                "status_check": "VFD ramp control supported"
            }
        ],
        "provenance": ProvenanceType.CONFIGURED.value
    }
