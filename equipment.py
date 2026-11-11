"""API Router for Equipment Configuration & Inventory."""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.entities import Equipment, AuditLog
from app.schemas.domain import EquipmentSchema, EquipmentUpdate
from app.core.provenance import EquipmentCriticality, ProvenanceType

router = APIRouter(prefix="/equipment", tags=["Equipment"])

@router.get("/", response_model=List[EquipmentSchema])
def list_equipment(db: Session = Depends(get_db)):
    return db.query(Equipment).all()

@router.get("/{equipment_id}", response_model=EquipmentSchema)
def get_equipment(equipment_id: str, db: Session = Depends(get_db)):
    eq = db.query(Equipment).filter_by(id=equipment_id).first()
    if not eq:
        raise HTTPException(status_code=404, detail=f"Equipment '{equipment_id}' not found")
    return eq

@router.put("/{equipment_id}", response_model=EquipmentSchema)
def update_equipment(equipment_id: str, payload: EquipmentUpdate, db: Session = Depends(get_db)):
    eq = db.query(Equipment).filter_by(id=equipment_id).first()
    if not eq:
        raise HTTPException(status_code=404, detail=f"Equipment '{equipment_id}' not found")
        
    update_data = payload.model_dump(exclude_unset=True)
    
    # HARD BOUNDARY ENFORCEMENT: Critical loads permanent exclusion
    if "criticality" in update_data:
        eq.criticality = update_data["criticality"]
        if eq.criticality == EquipmentCriticality.CRITICAL:
            eq.eligible_for_shutdown = False # HARD RULE: cannot be eligible if critical
            
    if "eligible_for_shutdown" in update_data:
        if eq.criticality == EquipmentCriticality.CRITICAL:
            eq.eligible_for_shutdown = False # Hard rule override
        else:
            eq.eligible_for_shutdown = update_data["eligible_for_shutdown"]
            
    for k, v in update_data.items():
        if k not in ("criticality", "eligible_for_shutdown"):
            setattr(eq, k, v)
            
    eq.provenance = ProvenanceType.CONFIGURED
    
    audit = AuditLog(
        user_id="ADMIN",
        role="ADMIN",
        action="UPDATE_EQUIPMENT",
        entity="EQUIPMENT",
        entity_id=equipment_id,
        details=update_data,
        provenance=ProvenanceType.CONFIGURED
    )
    db.add(audit)
    db.commit()
    db.refresh(eq)
    return eq
