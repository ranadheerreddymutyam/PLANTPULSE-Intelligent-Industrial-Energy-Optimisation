"""API Router for Dashboard Analytics and Aggregations."""
from fastapi import APIRouter, Depends
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.database import get_db
from app.models.entities import Equipment, Telemetry, IdlePeriod, Approval, Event, SiteConfig
from app.engineering.calculations import compute_idle_share, compute_estimated_savings
from app.core.provenance import ProvenanceType, OperatingState, EquipmentCriticality

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/dashboard-overview")
def get_dashboard_overview(db: Session = Depends(get_db)):
    """Computes real-time key metrics and sparklines for the main Executive Dashboard."""
    site = db.query(SiteConfig).first()
    equipment_list = db.query(Equipment).all()
    approvals = db.query(Approval).all()
    events = db.query(Event).all()
    idle_periods = db.query(IdlePeriod).all()
    
    # Latest telemetry per equipment
    latest_samples = []
    total_active_kw = 0.0
    total_apparent_kva = 0.0
    total_site_kwh = 0.0
    total_current_a = 0.0
    voltages = []
    power_factors = []
    
    state_counts = {
        "RUNNING": 0,
        "IDLE": 0,
        "STOPPED": 0
    }
    
    idle_equipment_names = []
    
    for eq in equipment_list:
        latest = (
            db.query(Telemetry)
            .filter_by(equipment_id=eq.id)
            .order_by(desc(Telemetry.timestamp))
            .first()
        )
        if latest:
            latest_samples.append(latest)
            total_active_kw += latest.active_power_kw
            total_apparent_kva += latest.apparent_power_kva
            total_site_kwh += latest.cumulative_energy_kwh
            total_current_a += latest.current_a
            voltages.append(latest.voltage_v)
            power_factors.append(latest.power_factor)
            
            st = latest.operating_state.value
            state_counts[st] = state_counts.get(st, 0) + 1
            if st == "IDLE":
                idle_equipment_names.append(eq.name)
                
    avg_voltage = round(sum(voltages) / len(voltages), 1) if voltages else 415.0
    avg_pf = round(sum(power_factors) / len(power_factors), 3) if power_factors else 0.85
    
    # Idle & Avoidable Energy aggregations
    total_idle_kwh = sum(p.total_idle_energy_kwh for p in idle_periods)
    total_avoidable_kwh = sum(p.avoidable_energy_kwh for p in idle_periods if p.eligible)
    
    idle_share_eng = compute_idle_share(total_idle_kwh, total_site_kwh)
    savings = compute_estimated_savings(
        avoidable_idle_kwh=total_avoidable_kwh,
        restart_allowance_kwh=site.restart_allowance_kwh if site else 0.0,
        tariff_per_kwh=site.tariff_per_kwh if site else 0.18,
        emission_factor_kg_co2_per_kwh=site.emission_factor_kg_co2_per_kwh if site else 0.42,
        currency=site.currency if site else "USD"
    )
    
    pending_approvals_count = sum(1 for a in approvals if a.status == "PENDING")
    active_events_count = sum(1 for e in events if e.status == "ACTIVE")
    
    # Sparkline: last 30 minutes of aggregate site power
    # Sample last 30 distinct timestamps
    recent_ts = (
        db.query(Telemetry.timestamp)
        .order_by(desc(Telemetry.timestamp))
        .distinct()
        .limit(30)
        .all()
    )
    
    sparkline_points = []
    for (ts,) in reversed(recent_ts):
        telems = db.query(Telemetry).filter_by(timestamp=ts).all()
        step_kw = sum(t.active_power_kw for t in telems)
        step_idle_kw = sum(t.active_power_kw for t in telems if t.operating_state == OperatingState.IDLE)
        sparkline_points.append({
            "timestamp": ts.isoformat(),
            "total_kw": round(step_kw, 2),
            "idle_kw": round(step_idle_kw, 2)
        })
        
    headline_sentence = (
        f"{state_counts['IDLE']} of {len(equipment_list)} equipment currently idle; "
        f"{round(total_avoidable_kwh, 2)} kWh avoidable idle energy identified in selected period — SIMULATED"
    )
    
    return {
        "project_status": "PROPOSED CONCEPT · DESIGN STAGE · NO RESULTS CLAIMED YET",
        "data_provenance": "SIMULATED / DEMONSTRATION DATA",
        "headline_sentence": headline_sentence,
        "site_id": site.id if site else "site_demo_01",
        "site_name": site.site_name if site else "Industrial Manufacturing Feeder A",
        "total_active_kw": round(total_active_kw, 2),
        "total_apparent_kva": round(total_apparent_kva, 2),
        "total_site_kwh": round(total_site_kwh, 2),
        "total_current_a": round(total_current_a, 1),
        "avg_voltage_v": avg_voltage,
        "avg_power_factor": avg_pf,
        "equipment_by_state": state_counts,
        "idle_equipment_count": state_counts["IDLE"],
        "idle_equipment_names": idle_equipment_names,
        "total_equipment_count": len(equipment_list),
        "total_idle_energy_kwh": round(total_idle_kwh, 2),
        "avoidable_idle_energy_kwh": round(total_avoidable_kwh, 2),
        "idle_share_percent": idle_share_eng.value,
        "savings": savings,
        "pending_approvals_count": pending_approvals_count,
        "active_events_count": active_events_count,
        "sparkline": sparkline_points,
        "provenance": ProvenanceType.DERIVED.value
    }
