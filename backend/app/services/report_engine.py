"""Report Engine for PlantPulse.

Generates official Prototype Engineering Assessments directly from live database tables.
Strictly transparent regarding assumptions, boundaries, and pilot roadmap.
"""
from datetime import datetime, timezone
from typing import Dict, Any, List
from app.core.provenance import ProvenanceType, EquipmentCriticality
from app.models.entities import (
    SiteConfig, Equipment, Telemetry, IdlePeriod, Decision, Approval, Event,
    BaselineRun, Report
)
from app.engineering.calculations import compute_before_after_saving_percentage

def generate_live_energy_assessment(db_session: Any) -> Dict[str, Any]:
    """Compiles a complete assessment from live database values."""
    site = db_session.query(SiteConfig).first()
    equipment_list = db_session.query(Equipment).all()
    idle_periods = db_session.query(IdlePeriod).all()
    events = db_session.query(Event).all()
    approvals = db_session.query(Approval).all()
    decisions = db_session.query(Decision).all()
    baseline_runs = db_session.query(BaselineRun).all()
    
    # Aggregate live numbers
    total_idle_kwh = sum(p.total_idle_energy_kwh for p in idle_periods)
    total_avoidable_kwh = sum(p.avoidable_energy_kwh for p in idle_periods if p.eligible)
    
    # Equipment ranking by avoidable kWh
    eq_ranking = []
    for eq in equipment_list:
        eq_periods = [p for p in idle_periods if p.equipment_id == eq.id]
        eq_idle_kwh = sum(p.total_idle_energy_kwh for p in eq_periods)
        eq_avoidable_kwh = sum(p.avoidable_energy_kwh for p in eq_periods if p.eligible)
        eq_ranking.append({
            "equipment_id": eq.id,
            "equipment_name": eq.name,
            "equipment_type": eq.equipment_type,
            "criticality": eq.criticality.value,
            "eligible": eq.eligible_for_shutdown,
            "idle_energy_kwh": round(eq_idle_kwh, 3),
            "avoidable_energy_kwh": round(eq_avoidable_kwh, 3),
            "p_idle_threshold_kw": eq.p_idle_threshold_kw,
            "t_delay_seconds": eq.t_delay_seconds
        })
        
    eq_ranking.sort(key=lambda x: x["avoidable_energy_kwh"], reverse=True)
    
    # Financial and emission calculations
    tariff = site.tariff_per_kwh if site else 0.18
    currency = site.currency if site else "USD"
    emission_factor = site.emission_factor_kg_co2_per_kwh if site else 0.42
    restart_allowance = site.restart_allowance_kwh if site else 0.0
    
    net_saving_kwh = max(0.0, total_avoidable_kwh - restart_allowance)
    est_cost_savings = net_saving_kwh * tariff
    est_co2_savings_kg = net_saving_kwh * emission_factor
    
    # Baseline comparison (find latest baseline vs optimised if available)
    baseline_run = next((r for r in reversed(baseline_runs) if r.run_type == "BASELINE"), None)
    optimised_run = next((r for r in reversed(baseline_runs) if r.run_type == "OPTIMISED"), None)
    
    comparison_data = None
    if baseline_run and optimised_run and baseline_run.seed == optimised_run.seed:
        pct_res = compute_before_after_saving_percentage(baseline_run.total_energy_kwh, optimised_run.total_energy_kwh)
        comparison_data = {
            "baseline_total_kwh": baseline_run.total_energy_kwh,
            "optimised_total_kwh": optimised_run.total_energy_kwh,
            "actual_saved_kwh": round(baseline_run.total_energy_kwh - optimised_run.total_energy_kwh, 2),
            "saving_percentage": pct_res.value,
            "fairness_note": f"Evaluated under identical seed ({baseline_run.seed}) and identical load schedule."
        }
        
    report_data = {
        "report_id": f"REP-{int(datetime.now(timezone.utc).timestamp())}",
        "title": "PLANTPULSE Energy Assessment",
        "header_banner": "PROTOTYPE ENGINEERING ASSESSMENT — SIMULATED DATA",
        "project_status": "PROPOSED CONCEPT · DESIGN STAGE · NO RESULTS CLAIMED YET",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model_version": "1.0.0-prototype",
        "provenance": ProvenanceType.DERIVED.value,
        
        # Site Metadata
        "site": {
            "site_id": site.id if site else "site_demo_01",
            "site_name": site.site_name if site else "Industrial Manufacturing Feeder A",
            "nominal_voltage_v": site.nominal_voltage_v if site else 415.0,
            "nominal_frequency_hz": site.nominal_frequency_hz if site else 50.0,
            "tariff_per_kwh": tariff,
            "currency": currency,
            "emission_factor_kg_co2_per_kwh": emission_factor,
            "restart_allowance_kwh": restart_allowance
        },
        
        # Deliverable 1: Baseline Data Needed
        "baseline_data_needed": [
            {"parameter": "3-Phase Line-to-Line Voltage (V_LL)", "purpose": "Apparent and active power derivation (415 V nominal balanced assumption)"},
            {"parameter": "3-Phase Line Current (I_line)", "purpose": "Thermal loading and power calculation"},
            {"parameter": "Active Power (kW)", "purpose": "Direct electrical signature monitoring and energy integration"},
            {"parameter": "Displacement Power Factor (PF)", "purpose": "Distinguishing loaded vs unloaded magnetizing current"},
            {"parameter": "Operating Frequency (Hz)", "purpose": "Supply stability and sensor health validation"},
            {"parameter": "Continuous Equipment Status (RUN / IDLE / STOP)", "purpose": "Prevent false idle flags during intentional shutdown"},
            {"parameter": "Safety Interlock Flags (E-Stop, Overload, Permissive)", "purpose": "Prevent automated commands during plant safety events"}
        ],
        
        # Deliverable 4: Measures Block
        "measures": {
            "total_idle_energy_kwh": round(total_idle_kwh, 2),
            "avoidable_idle_energy_kwh": round(total_avoidable_kwh, 2),
            "estimated_net_saving_kwh": round(net_saving_kwh, 2),
            "estimated_cost_savings": round(est_cost_savings, 2),
            "estimated_emissions_reduction_kg_co2": round(est_co2_savings_kg, 2),
            "out_of_scope_notice": "Water use / material loss / waste generated: Not in scope of current prototype (energy only)."
        },
        
        # Three Consideration Questions
        "consideration_questions": {
            "q1_where_loss_occurs": {
                "question": "Where does the loss occur?",
                "answer": "Loss occurs predominantly in auxiliary motors, fans, and conveyor drives that remain energized during meal breaks, shift handovers, and line standby.",
                "ranked_equipment": eq_ranking
            },
            "q2_can_practices_reduce": {
                "question": "Can process, equipment, planning, or employee practices reduce it?",
                "answer": "Yes. A combination of: (1) Process planning to align auxiliary runtimes with production batches; (2) Equipment retrofit with VFDs and auto-standby contactor relays; (3) Operator awareness workflows enabling one-click approved shutdown during scheduled pauses."
            },
            "q3_tradeoffs_to_check": {
                "question": "What trade-offs should be checked?",
                "tradeoffs": [
                    {"tradeoff": "Motor Restart Wear", "detail": "Frequent stopping and starting causes inrush currents up to 6-8x rated, heating windings. Mitigation: strict max restarts/hour limit (max 4/hr)."},
                    {"tradeoff": "Process Restart Delay", "detail": "Restarting air compressors or fans requires line pressurization and spin-up time. Mitigation: configurable t_delay and pre-shift warning alerts."},
                    {"tradeoff": "Safety & Critical Loads", "detail": "Cooling pumps and scrubber fans cannot be stopped without environmental or thermal hazard. Mitigation: permanent exclusion of CRITICAL equipment from automated control."}
                ]
            }
        },
        
        # Baseline Comparison
        "baseline_comparison": comparison_data,
        
        # Deliverable 3: Pilot Plan
        "pilot_plan": {
            "methodology_steps": [
                {"step": 1, "title": "Baseline Energy Measurement", "description": "Continuous 2-4 week non-intrusive electrical logging without control interventions."},
                {"step": 2, "title": "Idle-Period Monitoring & Signature Calibration", "description": "Calibrate individual P_idle thresholds and t_delay against recorded production duty cycles."},
                {"step": 3, "title": "Before-and-After Comparison", "description": "Implement operator-approved simulated or pilot contactor shutdowns under identical shift production volumes."},
                {"step": 4, "title": "Verification Under Comparable Conditions", "description": "Normalize against ambient temperature and product output to prove genuine net kWh reduction."}
            ],
            "roadmap_stages": [
                {"stage": 1, "name": "System Design", "status": "IN PROGRESS"},
                {"stage": 2, "name": "Component Selection (VT/CT, IC, Relays)", "status": "PLANNED / NOT IMPLEMENTED"},
                {"stage": 3, "name": "Prototype Hardware Development", "status": "PLANNED / NOT IMPLEMENTED"},
                {"stage": 4, "name": "Functional Testing in Test Cell", "status": "PLANNED / NOT IMPLEMENTED"},
                {"stage": 5, "name": "Industrial Pilot Validation", "status": "PLANNED / NOT IMPLEMENTED"},
                {"stage": 6, "name": "Industrial Multi-Site Deployment", "status": "PLANNED / NOT IMPLEMENTED"}
            ]
        },
        
        # Activity summaries
        "activity_summary": {
            "total_equipment_monitored": len(equipment_list),
            "critical_equipment_count": sum(1 for e in equipment_list if e.criticality == EquipmentCriticality.CRITICAL),
            "qualifying_idle_periods_count": len(idle_periods),
            "pending_approvals_count": sum(1 for a in approvals if a.status == "PENDING"),
            "approved_shutdowns_count": sum(1 for a in approvals if a.status == "APPROVED"),
            "active_alert_events_count": sum(1 for ev in events if ev.status == "ACTIVE")
        }
    }
    
    return report_data
