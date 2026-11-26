"""API Router for Simulated Contactor & VFD Control and Operator Approvals."""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.database import get_db
from app.models.entities import (
    Approval, ControlCommand, Equipment, Telemetry, AuditLog
)
from app.schemas.domain import (
    ApprovalSchema, ApprovalActionRequest, SimulatedCommandRequest, ControlCommandSchema
)
from app.core.provenance import UserRole, EquipmentCriticality, ProvenanceType, OperatingState

router = APIRouter(prefix="/control", tags=["Control & Safety (Simulated)"])

def utcnow():
    return datetime.now(timezone.utc)

@router.get("/approvals", response_model=List[ApprovalSchema])
def list_approvals(status_filter: Optional[str] = None, db: Session = Depends(get_db)):
    """Lists pending or historical operator approval requests."""
    query = db.query(Approval)
    if status_filter:
        query = query.filter_by(status=status_filter.upper())
    return query.order_by(desc(Approval.requested_at)).all()

@router.post("/approvals/{approval_id}/action", response_model=ApprovalSchema)
def review_approval(approval_id: int, payload: ApprovalActionRequest, db: Session = Depends(get_db)):
    """Operator reviews and approves or rejects a controlled shutdown recommendation."""
    approval = db.query(Approval).filter_by(id=approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found")
        
    action_upper = payload.action.upper()
    if action_upper not in ("APPROVE", "REJECT"):
        raise HTTPException(status_code=400, detail="Action must be 'APPROVE' or 'REJECT'")
        
    # Check equipment criticality safeguard
    eq = db.query(Equipment).filter_by(id=approval.equipment_id).first()
    if not eq:
        raise HTTPException(status_code=404, detail="Associated equipment not found")
        
    if eq.criticality == EquipmentCriticality.CRITICAL and action_upper == "APPROVE":
        raise HTTPException(
            status_code=403,
            detail="CRITICAL LOAD HARD LOCK: Controlled shutdown of critical equipment is permanently forbidden."
        )
        
    # Check active interlocks
    latest_tel = (
        db.query(Telemetry)
        .filter_by(equipment_id=eq.id)
        .order_by(desc(Telemetry.timestamp))
        .first()
    )
    if latest_tel and (latest_tel.interlock_estop or latest_tel.interlock_overload) and action_upper == "APPROVE":
        raise HTTPException(
            status_code=400,
            detail="INTERLOCK BLOCKED: Safety interlock (E-Stop/Overload) is active on this circuit."
        )
        
    approval.status = "APPROVED" if action_upper == "APPROVE" else "REJECTED"
    approval.reviewed_at = utcnow()
    approval.reviewed_by = payload.user_id
    approval.user_role = payload.user_role
    approval.comment = payload.comment
    
    # If approved, dispatch SIMULATED command
    if action_upper == "APPROVE":
        sim_cmd = ControlCommand(
            equipment_id=eq.id,
            approval_id=approval.id,
            command_type="SIMULATED_SHUTDOWN",
            target_interface="SIMULATED_CONTACTOR_VFD",
            simulated_command_label="SIMULATED COMMAND",
            status="EXECUTED",
            issued_by=f"{payload.user_id} ({payload.user_role.value})",
            issued_at=utcnow(),
            completed_at=utcnow(),
            details={
                "relay_signal": "OPEN_CIRCUIT",
                "simulated_notice": "NO PHYSICAL RELAY ACTUATED — SIMULATED ADAPTER ONLY",
                "comment": payload.comment
            },
            provenance=ProvenanceType.SIMULATED
        )
        db.add(sim_cmd)
        
        # Update latest telemetry operating state to STOPPED in simulation
        if latest_tel:
            latest_tel.operating_state = OperatingState.STOPPED
            latest_tel.active_power_kw = 0.0
            latest_tel.current_a = 0.0
            
    # Audit trail
    audit = AuditLog(
        user_id=payload.user_id,
        role=payload.user_role.value,
        action=f"{action_upper}_CONTROLLED_SHUTDOWN",
        entity="APPROVAL",
        entity_id=str(approval_id),
        details={"comment": payload.comment, "equipment_id": eq.id},
        provenance=ProvenanceType.DERIVED
    )
    db.add(audit)
    db.commit()
    db.refresh(approval)
    return approval

@router.post("/simulated-command", response_model=ControlCommandSchema)
def issue_simulated_command(payload: SimulatedCommandRequest, db: Session = Depends(get_db)):
    """Issues a direct simulated control action (Restart or Manual Override).
    NEVER sends signals to physical hardware.
    """
    eq = db.query(Equipment).filter_by(id=payload.equipment_id).first()
    if not eq:
        raise HTTPException(status_code=404, detail="Equipment not found")
        
    cmd_type = payload.command_type.upper()
    if cmd_type not in ("SIMULATED_SHUTDOWN", "SIMULATED_RESTART", "MANUAL_OVERRIDE"):
        raise HTTPException(status_code=400, detail="Invalid simulated command type")
        
    # Safeguard: Shutdown of critical load is permanently forbidden
    if cmd_type == "SIMULATED_SHUTDOWN" and eq.criticality == EquipmentCriticality.CRITICAL:
        raise HTTPException(
            status_code=403,
            detail="CRITICAL LOAD HARD LOCK: Controlled shutdown is forbidden for critical equipment."
        )
        
    cmd = ControlCommand(
        equipment_id=eq.id,
        command_type=cmd_type,
        target_interface="SIMULATED_CONTACTOR_VFD",
        simulated_command_label="SIMULATED COMMAND",
        status="EXECUTED",
        issued_by=f"{payload.user_id} ({payload.user_role.value})",
        issued_at=utcnow(),
        completed_at=utcnow(),
        details={
            "notice": "Simulated contactor adapter test command. No physical equipment controlled.",
            "reason": payload.reason
        },
        provenance=ProvenanceType.SIMULATED
    )
    db.add(cmd)
    
    audit = AuditLog(
        user_id=payload.user_id,
        role=payload.user_role.value,
        action=f"ISSUE_{cmd_type}",
        entity="EQUIPMENT",
        entity_id=eq.id,
        details={"reason": payload.reason},
        provenance=ProvenanceType.SIMULATED
    )
    db.add(audit)
    db.commit()
    db.refresh(cmd)
    return cmd

@router.get("/commands", response_model=List[ControlCommandSchema])
def list_control_commands(db: Session = Depends(get_db)):
    """Returns log of all executed simulated contactor/VFD commands."""
    return db.query(ControlCommand).order_by(desc(ControlCommand.issued_at)).limit(100).all()

@router.get("/interlocks")
def get_interlocks_status(db: Session = Depends(get_db)):
    """Returns real-time status of simulated interlocks for all site equipment."""
    equipment_list = db.query(Equipment).all()
    results = []
    
    for eq in equipment_list:
        latest_tel = (
            db.query(Telemetry)
            .filter_by(equipment_id=eq.id)
            .order_by(desc(Telemetry.timestamp))
            .first()
        )
        results.append({
            "equipment_id": eq.id,
            "equipment_name": eq.name,
            "criticality": eq.criticality.value,
            "eligible_for_shutdown": eq.eligible_for_shutdown,
            "estop_active": latest_tel.interlock_estop if latest_tel else False,
            "overload_active": latest_tel.interlock_overload if latest_tel else False,
            "process_permissive": latest_tel.interlock_process_permissive if latest_tel else True,
            "manual_override_active": latest_tel.interlock_manual_override if latest_tel else False,
            "can_shutdown": (
                eq.eligible_for_shutdown and
                eq.criticality != EquipmentCriticality.CRITICAL and
                not (latest_tel.interlock_estop or latest_tel.interlock_overload) if latest_tel else False
            )
        })
        
    return {
        "interlocks": results,
        "notice": "Simulated hardware interlocks monitoring panel. All status values are software-simulated.",
        "provenance": ProvenanceType.SIMULATED.value
    }
