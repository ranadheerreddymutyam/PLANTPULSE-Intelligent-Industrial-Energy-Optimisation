"""API Router for Engineering Assessment Reports."""
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from typing import List, Dict, Any, Optional
import json
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.database import get_db
from app.models.entities import Report, AuditLog
from app.schemas.domain import ReportSchema
from app.services.report_engine import generate_live_energy_assessment
from app.core.provenance import ProvenanceType

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/assessment")
def get_live_assessment(db: Session = Depends(get_db)):
    """Generates the official 'PLANTPULSE Energy Assessment' from LIVE database values."""
    return generate_live_energy_assessment(db)

@router.post("/save", response_model=ReportSchema)
def save_report_snapshot(title: Optional[str] = None, db: Session = Depends(get_db)):
    """Saves a permanent snapshot of the current live assessment in the database."""
    assessment = generate_live_energy_assessment(db)
    rep_id = assessment["report_id"]
    rep_title = title or assessment["title"]
    
    rep = Report(
        id=rep_id,
        title=rep_title,
        report_type="ENERGY_ASSESSMENT",
        scenario_id=assessment["site"].get("site_id"),
        data=assessment,
        provenance=ProvenanceType.DERIVED,
        model_version=assessment["model_version"]
    )
    db.add(rep)
    
    audit = AuditLog(
        user_id="ENERGY_MGR",
        role="ENERGY_MANAGER",
        action="GENERATE_REPORT",
        entity="REPORT",
        entity_id=rep_id,
        details={"title": rep_title},
        provenance=ProvenanceType.DERIVED
    )
    db.add(audit)
    db.commit()
    db.refresh(rep)
    return rep

@router.get("/history", response_model=List[ReportSchema])
def list_reports(db: Session = Depends(get_db)):
    return db.query(Report).order_by(desc(Report.generated_at)).limit(20).all()

@router.get("/{report_id}/export-json")
def export_report_json(report_id: str, db: Session = Depends(get_db)):
    rep = db.query(Report).filter_by(id=report_id).first()
    data = rep.data if rep else generate_live_energy_assessment(db)
    json_str = json.dumps(data, indent=2)
    return Response(
        content=json_str,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={report_id}_energy_assessment.json"}
    )
