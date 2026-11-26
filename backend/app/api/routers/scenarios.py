"""API Router for Scenarios and Deterministic Simulations."""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.entities import Scenario
from app.schemas.domain import ScenarioSchema, ScenarioSwitchRequest
from app.services.scenario_engine import generate_scenario_telemetry

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])

@router.get("/", response_model=List[ScenarioSchema])
def list_scenarios(db: Session = Depends(get_db)):
    """Lists all 7 operational scenarios."""
    return db.query(Scenario).all()

@router.post("/switch")
def switch_scenario(payload: ScenarioSwitchRequest, db: Session = Depends(get_db)):
    """Switches the active operational scenario.
    Regenerates deterministic physical telemetry and cascades through calculations,
    idle periods, decisions, events, and savings.
    """
    scen = db.query(Scenario).filter_by(id=payload.scenario_id).first()
    if not scen:
        raise HTTPException(status_code=404, detail=f"Scenario '{payload.scenario_id}' not found")
        
    try:
        result = generate_scenario_telemetry(db, payload.scenario_id)
        return {
            "status": "success",
            "message": f"Switched to '{scen.name}'. Telemetry and calculations refreshed across all pages.",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scenario regeneration failed: {str(e)}")
