"""Deterministic Synthetic Data Engine for PlantPulse.

Generates physically-coupled electrical telemetry for 7 distinct industrial scenarios.
Formulas adhere to: P = sqrt(3) * V_LL * I * PF / 1000.
Strictly non-AI, seed-based, reproducible simulation.
"""
import math
import random
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from app.core.provenance import (
    ProvenanceType, OperatingState, EquipmentCriticality, DecisionOutcome
)
from app.engineering.calculations import (
    SQRT3, compute_apparent_power, compute_active_power, compute_power_factor,
    compute_reactive_power, evaluate_idle_periods, compute_estimated_savings,
    compute_idle_share, compute_before_after_saving_percentage
)
from app.models.entities import (
    SiteConfig, Equipment, Telemetry, IdlePeriod, Decision, Approval,
    ControlCommand, Event, Scenario, BaselineRun, DataQualityCheck, AuditLog
)
from app.services.logical_flow import evaluate_logical_flow
from app.services.alert_engine import alert_engine

SCENARIO_DEFINITIONS = [
    {
        "id": "scenario_normal_shift",
        "name": "Normal Shift Operation",
        "description": "Standard production shift with high active equipment duty, minimal transient pauses, and low idle duration.",
        "seed": 101,
        "duration_hours": 8.0
    },
    {
        "id": "scenario_heavy_idle",
        "name": "Heavy Idle Operation (Baseline)",
        "description": "Unattended lunch breaks, shift handovers, and night pauses where non-critical motors and fans run sustained idle.",
        "seed": 202,
        "duration_hours": 8.0
    },
    {
        "id": "scenario_intermittent_short",
        "name": "Intermittent Short Idle",
        "description": "Frequent brief equipment pauses (30-80s) strictly below configured t_delay. Verifies delay filter prevents false trips.",
        "seed": 303,
        "duration_hours": 8.0
    },
    {
        "id": "scenario_critical_load_idle",
        "name": "Critical Load Idle",
        "description": "Low active power on critical process cooling and safety motors. Verifies permanent exclusion of critical assets.",
        "seed": 404,
        "duration_hours": 8.0
    },
    {
        "id": "scenario_interlock_blocked",
        "name": "Interlock Blocked",
        "description": "Sustained idle present on eligible assets, but E-stop or thermal overload circuits are tripped, inhibiting shutdown.",
        "seed": 505,
        "duration_hours": 8.0
    },
    {
        "id": "scenario_sensor_fault",
        "name": "Sensor / Data Fault",
        "description": "Severe voltage sag/swell and PT/CT sensor anomalies. Verifies Step 2 electrical parameter rejection and data-quality logging.",
        "seed": 606,
        "duration_hours": 8.0
    },
    {
        "id": "scenario_optimised_run",
        "name": "Optimised Run (Controlled Shutdown Applied)",
        "description": "Identical seed and load pattern as Heavy Idle Baseline, with operator-approved simulated contactor shutdowns applied.",
        "seed": 202, # Exactly same seed as heavy idle for 100% fair baseline comparison
        "duration_hours": 8.0
    }
]

def utcnow():
    return datetime.now(timezone.utc)

def generate_scenario_telemetry(
    db_session: Any,
    scenario_id: str
) -> Dict[str, Any]:
    """Generates deterministic physical telemetry for all site equipment under the chosen scenario."""
    scen_def = next((s for s in SCENARIO_DEFINITIONS if s["id"] == scenario_id), SCENARIO_DEFINITIONS[1])
    rng = random.Random(scen_def["seed"])
    
    site = db_session.query(SiteConfig).first()
    if not site:
        raise ValueError("SiteConfig not found. Please run seed script first.")
        
    equipment_list = db_session.query(Equipment).all()
    if not equipment_list:
        raise ValueError("No equipment found in database.")
        
    # Clear existing telemetry, idle periods, decisions, events for this scenario (or all if active)
    db_session.query(Telemetry).delete()
    db_session.query(IdlePeriod).delete()
    db_session.query(Decision).delete()
    db_session.query(Event).delete()
    db_session.query(DataQualityCheck).delete()
    db_session.query(Approval).delete()
    db_session.query(ControlCommand).delete()
    db_session.commit()
    
    # Mark scenario active
    for sc in db_session.query(Scenario).all():
        sc.is_active = (sc.id == scenario_id)
    db_session.commit()
    
    start_time = utcnow() - timedelta(hours=scen_def["duration_hours"])
    sample_interval_s = 60.0 # 1 sample per minute
    total_samples = int((scen_def["duration_hours"] * 3600) / sample_interval_s)
    
    all_telemetry: List[Telemetry] = []
    equipment_telemetry_series: Dict[str, Dict[str, list]] = {}
    
    for eq in equipment_list:
        equipment_telemetry_series[eq.id] = {
            "timestamps_epoch": [],
            "powers_kw": [],
            "states": [],
            "objects": []
        }
        
    is_optimised_scenario = (scenario_id == "scenario_optimised_run")
    
    # Simulate time step by time step
    for step in range(total_samples):
        current_time = start_time + timedelta(seconds=step * sample_interval_s)
        epoch_s = current_time.timestamp()
        
        # Grid line-to-line voltage with slight realistic variation
        grid_base_v = site.nominal_voltage_v + rng.uniform(-2.5, 2.5)
        grid_freq = site.nominal_frequency_hz + rng.uniform(-0.1, 0.1)
        
        # Scenario 6 sensor fault injection
        if scenario_id == "scenario_sensor_fault" and 60 <= step <= 120:
            grid_base_v = 510.0 # Overvoltage sensor anomaly
            grid_freq = 44.5    # Severe frequency sag
            
        for eq in equipment_list:
            rated_p = eq.rated_power_kw
            p_idle = eq.p_idle_threshold_kw
            t_delay = eq.t_delay_seconds
            is_critical = (eq.criticality == EquipmentCriticality.CRITICAL)
            
            # Interlock defaults
            estop = False
            overload = False
            permissive = True
            manual_override = False
            
            if scenario_id == "scenario_interlock_blocked" and not is_critical and 40 <= step <= 180:
                if eq.equipment_type == "fan":
                    estop = True
                elif eq.equipment_type == "pump":
                    overload = True
                    
            # Determine operating state & load pattern for this equipment at this step
            # Normal production active power ~ 70% to 90% of rated
            active_load_p = rated_p * rng.uniform(0.72, 0.92)
            # Idle power ~ 40% to 80% of P_idle threshold
            idle_load_p = p_idle * rng.uniform(0.45, 0.85)
            
            is_idle = False
            is_stopped = False
            
            if scenario_id == "scenario_normal_shift":
                # Only 1 brief break (steps 180 to 183 = 3 mins)
                if 180 <= step <= 183 and not is_critical:
                    is_idle = True
            elif scenario_id in ("scenario_heavy_idle", "scenario_optimised_run"):
                # Major sustained idle periods:
                # Break 1: steps 100 to 160 (60 minutes)
                # Break 2: steps 240 to 320 (80 minutes)
                if (100 <= step <= 160 or 240 <= step <= 320):
                    if not is_critical:
                        if is_optimised_scenario and step >= (100 + int(t_delay / sample_interval_s)):
                            # Under optimised scenario, controlled shutdown occurred after t_delay!
                            is_stopped = True
                        elif is_optimised_scenario and step >= (240 + int(t_delay / sample_interval_s)):
                            is_stopped = True
                        else:
                            is_idle = True
                    else:
                        # Critical equipment runs at partial process speed or normal
                        is_idle = False
            elif scenario_id == "scenario_intermittent_short":
                # Quick idle bursts of 1 minute each (60s < t_delay)
                if step % 20 in (0, 1):
                    is_idle = True
            elif scenario_id == "scenario_critical_load_idle":
                # Critical load idle for 2 hours (steps 100 to 220)
                if 100 <= step <= 220 and is_critical:
                    is_idle = True
            elif scenario_id == "scenario_interlock_blocked":
                if 40 <= step <= 180 and not is_critical:
                    is_idle = True
            elif scenario_id == "scenario_sensor_fault":
                if step % 30 == 0:
                    is_idle = True
                    
            # Compute physical parameters
            if is_stopped:
                active_p = 0.0
                pf = 0.0
                current_a = 0.0
                st = OperatingState.STOPPED
            elif is_idle:
                active_p = idle_load_p
                # Idle motor has low power factor due to dominant magnetizing inductance
                pf = round(rng.uniform(0.28, 0.42), 3)
                # Physical current: I = 1000 * P / (sqrt(3) * V * PF)
                current_a = round((1000.0 * active_p) / (SQRT3 * grid_base_v * pf), 2)
                st = OperatingState.IDLE
            else:
                active_p = active_load_p
                # Loaded motor has high power factor
                pf = round(rng.uniform(0.84, 0.91), 3)
                current_a = round((1000.0 * active_p) / (SQRT3 * grid_base_v * pf), 2)
                st = OperatingState.RUNNING
                
            apparent_kva = round((SQRT3 * grid_base_v * current_a) / 1000.0, 4)
            reactive_kvar = round(math.sqrt(max(0.0, (apparent_kva ** 2) - (active_p ** 2))), 4)
            
            # Cumulative energy (approximate accumulator)
            prev_e = equipment_telemetry_series[eq.id]["objects"][-1].cumulative_energy_kwh if equipment_telemetry_series[eq.id]["objects"] else 0.0
            inc_e = (active_p * (sample_interval_s / 3600.0))
            cum_e = round(prev_e + inc_e, 4)
            
            tel = Telemetry(
                equipment_id=eq.id,
                scenario_id=scenario_id,
                timestamp=current_time,
                timestamp_epoch_s=epoch_s,
                voltage_v=round(grid_base_v, 2),
                current_a=round(current_a, 2),
                power_factor=round(pf, 3),
                frequency_hz=round(grid_freq, 2),
                active_power_kw=round(active_p, 4),
                apparent_power_kva=apparent_kva,
                reactive_power_kvar=reactive_kvar,
                cumulative_energy_kwh=cum_e,
                operating_state=st,
                interlock_estop=estop,
                interlock_overload=overload,
                interlock_process_permissive=permissive,
                interlock_manual_override=manual_override,
                provenance=ProvenanceType.SIMULATED,
                model_version="1.0.0-prototype"
            )
            
            all_telemetry.append(tel)
            equipment_telemetry_series[eq.id]["timestamps_epoch"].append(epoch_s)
            equipment_telemetry_series[eq.id]["powers_kw"].append(active_p)
            equipment_telemetry_series[eq.id]["states"].append(st.value)
            equipment_telemetry_series[eq.id]["objects"].append(tel)
            
    # Bulk insert telemetry
    db_session.bulk_save_objects(all_telemetry)
    db_session.commit()
    
    # -----------------------------------------------------------------
    # Post-Process: Calculate Idle Periods & Avoidable Energy per Equipment
    # -----------------------------------------------------------------
    site_total_energy = 0.0
    site_total_idle_energy = 0.0
    site_total_avoidable_energy = 0.0
    
    for eq in equipment_list:
        data = equipment_telemetry_series[eq.id]
        idle_eval = evaluate_idle_periods(
            timestamps_epoch_s=data["timestamps_epoch"],
            powers_kw=data["powers_kw"],
            states=data["states"],
            p_idle_threshold_kw=eq.p_idle_threshold_kw,
            t_delay_seconds=eq.t_delay_seconds,
            is_eligible=eq.eligible_for_shutdown and (eq.criticality != EquipmentCriticality.CRITICAL)
        )
        
        # Save IdlePeriods in database
        for p in idle_eval["periods"]:
            start_dt = datetime.fromisoformat(p["start_time_iso"])
            end_dt = datetime.fromisoformat(p["end_time_iso"])
            ip_obj = IdlePeriod(
                equipment_id=eq.id,
                scenario_id=scenario_id,
                start_time=start_dt,
                end_time=end_dt,
                start_epoch_s=start_dt.timestamp(),
                end_epoch_s=end_dt.timestamp(),
                duration_seconds=p["duration_seconds"],
                p_idle_threshold_kw=eq.p_idle_threshold_kw,
                t_delay_seconds=eq.t_delay_seconds,
                total_idle_energy_kwh=p["idle_energy_kwh"],
                avoidable_energy_kwh=p["avoidable_energy_kwh"],
                eligible=p["eligible_for_shutdown"],
                provenance=ProvenanceType.DERIVED
            )
            db_session.add(ip_obj)
            
        eq_total_e = data["objects"][-1].cumulative_energy_kwh if data["objects"] else 0.0
        site_total_energy += eq_total_e
        site_total_idle_energy += idle_eval["total_idle_energy_kwh"].value or 0.0
        site_total_avoidable_energy += idle_eval["avoidable_idle_energy_kwh"].value or 0.0
        
        # -------------------------------------------------------------
        # Evaluate Logical Flow for latest sample and create trace
        # -------------------------------------------------------------
        latest_tel = data["objects"][-1]
        sample_dict = {
            "voltage_v": latest_tel.voltage_v,
            "current_a": latest_tel.current_a,
            "frequency_hz": latest_tel.frequency_hz,
            "power_factor": latest_tel.power_factor,
            "active_power_kw": latest_tel.active_power_kw,
            "operating_state": latest_tel.operating_state.value,
            "interlock_estop": latest_tel.interlock_estop,
            "interlock_overload": latest_tel.interlock_overload,
            "interlock_process_permissive": latest_tel.interlock_process_permissive,
            "interlock_manual_override": latest_tel.interlock_manual_override
        }
        
        # Check if an approval exists or create simulated approval if heavy idle
        simulated_approval = None
        if is_optimised_scenario and eq.eligible_for_shutdown and (eq.criticality != EquipmentCriticality.CRITICAL):
            simulated_approval = Approval(
                equipment_id=eq.id,
                scenario_id=scenario_id,
                action_type="SIMULATED_SHUTDOWN",
                status="APPROVED",
                requested_at=latest_tel.timestamp - timedelta(minutes=45),
                reviewed_at=latest_tel.timestamp - timedelta(minutes=40),
                reviewed_by="Operator John D.",
                user_role="OPERATOR",
                comment="Approved controlled shutdown during lunch break.",
                estimated_kwh_saving=idle_eval["avoidable_idle_energy_kwh"].value or 0.0,
                provenance=ProvenanceType.DERIVED
            )
            db_session.add(simulated_approval)
            db_session.flush()
            
            # Record simulated contactor command
            cmd = ControlCommand(
                equipment_id=eq.id,
                approval_id=simulated_approval.id,
                command_type="SIMULATED_SHUTDOWN",
                target_interface="SIMULATED_CONTACTOR_VFD",
                simulated_command_label="SIMULATED COMMAND",
                status="EXECUTED",
                issued_by="Operator John D.",
                issued_at=latest_tel.timestamp - timedelta(minutes=40),
                completed_at=latest_tel.timestamp - timedelta(minutes=40),
                details={"relay_channel": 2, "bus_voltage": latest_tel.voltage_v},
                provenance=ProvenanceType.SIMULATED
            )
            db_session.add(cmd)
            
        # Determine continuous idle duration for latest sample
        # Check backward from latest
        idle_count = 0
        for st_val, p_val in zip(reversed(data["states"]), reversed(data["powers_kw"])):
            if p_val < eq.p_idle_threshold_kw and st_val in ("RUNNING", "IDLE"):
                idle_count += 1
            else:
                break
        continuous_idle_s = idle_count * sample_interval_s
        
        # If scenario is heavy idle and eligible, create a pending approval in queue
        if scenario_id == "scenario_heavy_idle" and eq.eligible_for_shutdown and eq.criticality != EquipmentCriticality.CRITICAL and continuous_idle_s >= eq.t_delay_seconds:
            pending_app = Approval(
                equipment_id=eq.id,
                scenario_id=scenario_id,
                action_type="SIMULATED_SHUTDOWN",
                status="PENDING",
                requested_at=latest_tel.timestamp - timedelta(minutes=15),
                estimated_kwh_saving=idle_eval["avoidable_idle_energy_kwh"].value or 0.0,
                provenance=ProvenanceType.DERIVED
            )
            db_session.add(pending_app)
            db_session.flush()
            simulated_approval = pending_app
            
        flow_result = evaluate_logical_flow(
            equipment=eq,
            site_config=site,
            telemetry_sample=sample_dict,
            idle_continuous_seconds=continuous_idle_s,
            operator_approval=simulated_approval,
            recent_restarts_in_hour=1
        )
        
        dec_obj = Decision(
            equipment_id=eq.id,
            scenario_id=scenario_id,
            timestamp=latest_tel.timestamp,
            evaluation_step=flow_result["evaluation_step"],
            outcome=flow_result["outcome"],
            reason=flow_result["reason"],
            decision_trace=flow_result["decision_trace"],
            recommendation_text=flow_result.get("recommendation_text"),
            approval_required=flow_result.get("approval_required", False),
            approval_id=simulated_approval.id if simulated_approval else None,
            provenance=ProvenanceType.DERIVED
        )
        db_session.add(dec_obj)
        
        # If sensor fault scenario, log DataQualityCheck
        if flow_result["outcome"] == DecisionOutcome.REJECTED_INPUT_FAULT:
            dqc = DataQualityCheck(
                telemetry_id=latest_tel.id,
                equipment_id=eq.id,
                timestamp=latest_tel.timestamp,
                check_type="ELECTRICAL_PARAMETER_OUT_OF_SPEC",
                raw_payload=sample_dict,
                status="REJECTED",
                action_taken="Excluded from energy and idle integration; maintenance alert raised.",
                provenance=ProvenanceType.DERIVED
            )
            db_session.add(dqc)
            
        # Run alert engine on latest sample
        alert_engine.evaluate_telemetry_sample(db_session, eq, site, sample_dict, scenario_id=scenario_id)
        
    db_session.commit()
    
    # -------------------------------------------------------------
    # Record BaselineRun
    # -------------------------------------------------------------
    savings = compute_estimated_savings(
        avoidable_idle_kwh=site_total_avoidable_energy,
        restart_allowance_kwh=site.restart_allowance_kwh,
        tariff_per_kwh=site.tariff_per_kwh,
        emission_factor_kg_co2_per_kwh=site.emission_factor_kg_co2_per_kwh,
        currency=site.currency
    )
    
    idle_sh = compute_idle_share(site_total_idle_energy, site_total_energy)
    
    brun = BaselineRun(
        scenario_id=scenario_id,
        run_type="OPTIMISED" if is_optimised_scenario else "BASELINE",
        seed=scen_def["seed"],
        total_energy_kwh=round(site_total_energy, 4),
        idle_energy_kwh=round(site_total_idle_energy, 4),
        avoidable_energy_kwh=round(site_total_avoidable_energy, 4),
        estimated_savings_kwh=savings["energy_savings_kwh"].value or 0.0,
        estimated_cost_savings=savings["cost_savings"].value or 0.0,
        estimated_emissions_kg_co2=savings["emissions_reduction_kg_co2"].value or 0.0,
        idle_share_percent=idle_sh.value or 0.0,
        provenance=ProvenanceType.DERIVED
    )
    db_session.add(brun)
    
    # Audit log
    audit = AuditLog(
        user_id="SYSTEM",
        role="SYSTEM",
        action="SWITCH_SCENARIO",
        entity="SCENARIO",
        entity_id=scenario_id,
        details={"scenario_name": scen_def["name"], "seed": scen_def["seed"]},
        provenance=ProvenanceType.DERIVED
    )
    db_session.add(audit)
    db_session.commit()
    
    return {
        "scenario_id": scenario_id,
        "name": scen_def["name"],
        "total_energy_kwh": round(site_total_energy, 2),
        "idle_energy_kwh": round(site_total_idle_energy, 2),
        "avoidable_energy_kwh": round(site_total_avoidable_energy, 2),
        "savings": savings,
        "sample_count": len(all_telemetry)
    }
