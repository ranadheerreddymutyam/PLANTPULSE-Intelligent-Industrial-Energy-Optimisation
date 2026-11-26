"""API Router for Idle Energy Analysis."""
from fastapi import APIRouter, Depends, Query
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.database import get_db
from app.models.entities import IdlePeriod, Equipment, SiteConfig, Telemetry
from app.schemas.domain import IdlePeriodSchema
from app.engineering.calculations import compute_idle_share, compute_estimated_savings
from app.core.provenance import ProvenanceType, EquipmentCriticality

router = APIRouter(prefix="/idle", tags=["Idle Analysis"])

@router.get("/periods", response_model=List[IdlePeriodSchema])
def list_idle_periods(
    equipment_id: Optional[str] = None,
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(IdlePeriod)
    if equipment_id:
        query = query.filter_by(equipment_id=equipment_id)
    return query.order_by(desc(IdlePeriod.start_time)).limit(limit).all()

@router.get("/ranking")
def get_loss_ranking(db: Session = Depends(get_db)):
    """Answers the track question: 'Where does the loss occur?'
    Ranks equipment by avoidable idle kWh in the current dataset.
    """
    equipment_list = db.query(Equipment).all()
    periods = db.query(IdlePeriod).all()
    
    ranking = []
    total_avoidable_site = 0.0
    
    for eq in equipment_list:
        eq_periods = [p for p in periods if p.equipment_id == eq.id]
        eq_idle_kwh = sum(p.total_idle_energy_kwh for p in eq_periods)
        eq_avoidable_kwh = sum(p.avoidable_energy_kwh for p in eq_periods if p.eligible)
        eq_duration_s = sum(p.duration_seconds for p in eq_periods)
        total_avoidable_site += eq_avoidable_kwh
        
        ranking.append({
            "equipment_id": eq.id,
            "equipment_name": eq.name,
            "equipment_type": eq.equipment_type,
            "criticality": eq.criticality.value,
            "eligible_for_shutdown": eq.eligible_for_shutdown,
            "p_idle_threshold_kw": eq.p_idle_threshold_kw,
            "t_delay_seconds": eq.t_delay_seconds,
            "qualifying_periods_count": len(eq_periods),
            "total_idle_duration_minutes": round(eq_duration_s / 60.0, 1),
            "idle_energy_kwh": round(eq_idle_kwh, 3),
            "avoidable_idle_energy_kwh": round(eq_avoidable_kwh, 3),
            "provenance": ProvenanceType.ESTIMATED.value
        })
        
    ranking.sort(key=lambda x: x["avoidable_idle_energy_kwh"], reverse=True)
    
    for item in ranking:
        item["share_of_avoidable_percent"] = round(
            (item["avoidable_idle_energy_kwh"] / total_avoidable_site * 100.0) if total_avoidable_site > 0 else 0.0,
            1
        )
        
    return {
        "title": "Where does the loss occur? — Avoidable Idle Energy Ranking",
        "total_avoidable_idle_energy_kwh": round(total_avoidable_site, 3),
        "ranking": ranking,
        "provenance": ProvenanceType.ESTIMATED.value,
        "note": "Derived strictly from qualifying idle durations (t >= t_delay) on eligible non-critical assets."
    }

@router.get("/summary")
def get_idle_summary(db: Session = Depends(get_db)):
    site = db.query(SiteConfig).first()
    periods = db.query(IdlePeriod).all()
    latest_telemetry = db.query(Telemetry).all()
    
    total_idle_kwh = sum(p.total_idle_energy_kwh for p in periods)
    total_avoidable_kwh = sum(p.avoidable_energy_kwh for p in periods if p.eligible)
    
    # Calculate total energy
    total_site_kwh = 0.0
    for eq in db.query(Equipment).all():
        last_t = (
            db.query(Telemetry)
            .filter_by(equipment_id=eq.id)
            .order_by(desc(Telemetry.timestamp))
            .first()
        )
        if last_t:
            total_site_kwh += last_t.cumulative_energy_kwh
            
    idle_share_eng = compute_idle_share(total_idle_kwh, total_site_kwh)
    savings = compute_estimated_savings(
        avoidable_idle_kwh=total_avoidable_kwh,
        restart_allowance_kwh=site.restart_allowance_kwh if site else 0.0,
        tariff_per_kwh=site.tariff_per_kwh if site else 0.18,
        emission_factor_kg_co2_per_kwh=site.emission_factor_kg_co2_per_kwh if site else 0.42,
        currency=site.currency if site else "USD"
    )
    
    return {
        "total_energy_kwh": round(total_site_kwh, 2),
        "total_idle_energy_kwh": round(total_idle_kwh, 2),
        "avoidable_idle_energy_kwh": round(total_avoidable_kwh, 2),
        "idle_share_percent": idle_share_eng.value,
        "savings": savings,
        "provenance": ProvenanceType.DERIVED.value
    }
