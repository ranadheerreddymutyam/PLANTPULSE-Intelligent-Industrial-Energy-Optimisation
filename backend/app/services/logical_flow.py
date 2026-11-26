"""Logical Flow Engine (8 Steps + Decision Trace).

Deterministic, rule-based state machine evaluating electrical telemetry against
configured engineering thresholds. Strictly non-AI/ML.
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from app.core.provenance import (
    ProvenanceType, DecisionOutcome, OperatingState, EquipmentCriticality
)
from app.engineering.calculations import (
    compute_apparent_power, compute_active_power, compute_power_factor, compute_reactive_power
)

def evaluate_logical_flow(
    equipment: Any, # Equipment model or dict
    site_config: Any, # SiteConfig model or dict
    telemetry_sample: Dict[str, Any],
    idle_continuous_seconds: float = 0.0,
    operator_approval: Optional[Any] = None,
    recent_restarts_in_hour: int = 0,
    seconds_since_last_stop: Optional[float] = None
) -> Dict[str, Any]:
    """Executes the 8-step decision pipeline and generates an explainable decision trace."""
    
    trace: List[Dict[str, Any]] = []
    
    # -------------------------------------------------------------
    # STEP 1: INPUT ACQUISITION
    # -------------------------------------------------------------
    voltage_v = telemetry_sample.get("voltage_v")
    current_a = telemetry_sample.get("current_a")
    freq_hz = telemetry_sample.get("frequency_hz", 50.0)
    pf_in = telemetry_sample.get("power_factor", 0.85)
    kw_in = telemetry_sample.get("active_power_kw")
    raw_state = telemetry_sample.get("operating_state", "RUNNING")
    
    trace.append({
        "step_number": 1,
        "step_name": "Input Acquisition",
        "status": "PASSED",
        "evaluation": "Telemetry parameters successfully acquired from simulator/import pipeline.",
        "values": {
            "voltage_v": voltage_v,
            "current_a": current_a,
            "frequency_hz": freq_hz,
            "power_factor_input": pf_in,
            "metered_kw": kw_in,
            "raw_state": raw_state
        }
    })
    
    # -------------------------------------------------------------
    # STEP 2: ELECTRICAL PARAMETER VALIDATION
    # -------------------------------------------------------------
    v_min = getattr(site_config, "voltage_min_v", 373.5)
    v_max = getattr(site_config, "voltage_max_v", 456.5)
    f_min = getattr(site_config, "frequency_min_hz", 47.5)
    f_max = getattr(site_config, "frequency_max_hz", 52.5)
    rated_i = getattr(equipment, "rated_current_a", 100.0)
    i_max_limit = rated_i * 2.5 # extreme physical overcurrent limit
    
    validation_failures = []
    if voltage_v is None or not (v_min <= voltage_v <= v_max):
        validation_failures.append(f"Voltage {voltage_v} V outside allowable range [{v_min}, {v_max}] V")
    if current_a is None or current_a < 0 or current_a > i_max_limit:
        validation_failures.append(f"Current {current_a} A outside physical range [0, {i_max_limit}] A")
    if freq_hz is None or not (f_min <= freq_hz <= f_max):
        validation_failures.append(f"Frequency {freq_hz} Hz outside allowable range [{f_min}, {f_max}] Hz")
        
    if validation_failures:
        trace.append({
            "step_number": 2,
            "step_name": "Electrical Parameter Validation",
            "status": "FAILED",
            "evaluation": f"Sensor / input parameter validation failed: {'; '.join(validation_failures)}",
            "values": {"validation_failures": validation_failures}
        })
        return {
            "evaluation_step": 2,
            "outcome": DecisionOutcome.REJECTED_INPUT_FAULT,
            "reason": f"Input/sensor fault: {'; '.join(validation_failures)}. Excluded from energy analysis.",
            "decision_trace": trace,
            "recommendation_text": "Check sensor wiring, PT/CT calibration, and meter telemetry integrity.",
            "approval_required": False
        }
        
    trace.append({
        "step_number": 2,
        "step_name": "Electrical Parameter Validation",
        "status": "PASSED",
        "evaluation": "All electrical parameters within configured operational tolerances.",
        "values": {"voltage_v": voltage_v, "current_a": current_a, "frequency_hz": freq_hz}
    })
    
    # -------------------------------------------------------------
    # STEP 3: REAL-TIME POWER MONITORING
    # -------------------------------------------------------------
    s_eng = compute_apparent_power(voltage_v, current_a)
    p_eng = compute_active_power(voltage_v, current_a, pf_in, metered_kw=kw_in)
    pf_eng = compute_power_factor(p_eng.value, s_eng.value)
    q_eng = compute_reactive_power(s_eng.value, p_eng.value)
    
    p_active = p_eng.value or 0.0
    s_apparent = s_eng.value or 0.0
    pf_calc = pf_eng.value or 0.0
    
    trace.append({
        "step_number": 3,
        "step_name": "Real-Time Power Monitoring",
        "status": "PASSED",
        "evaluation": "Active, apparent, and reactive power derived via standard balanced 3-phase equations.",
        "values": {
            "apparent_power_kva": s_apparent,
            "active_power_kw": p_active,
            "power_factor": pf_calc,
            "reactive_power_kvar": q_eng.value
        }
    })
    
    # -------------------------------------------------------------
    # STEP 4: EQUIPMENT OPERATING-STATE DETECTION
    # -------------------------------------------------------------
    rated_p = getattr(equipment, "rated_power_kw", 50.0)
    p_idle_threshold = getattr(equipment, "p_idle_threshold_kw", rated_p * 0.20)
    
    if current_a < 0.05 * rated_i or str(raw_state).upper() in ("STOPPED", "STOP", "OFF"):
        detected_state = OperatingState.STOPPED
    elif p_active < p_idle_threshold:
        detected_state = OperatingState.IDLE
    else:
        detected_state = OperatingState.RUNNING
        
    trace.append({
        "step_number": 4,
        "step_name": "Equipment Operating-State Detection",
        "status": "PASSED",
        "evaluation": f"Operating state identified as {detected_state.value}.",
        "values": {"detected_state": detected_state.value, "p_active_kw": p_active, "rated_power_kw": rated_p}
    })
    
    if detected_state == OperatingState.STOPPED:
        return {
            "evaluation_step": 4,
            "outcome": DecisionOutcome.ACTIVELY_REQUIRED,
            "reason": "Equipment is stopped. Normal shutdown/idle standby. Keep monitoring.",
            "decision_trace": trace,
            "recommendation_text": "Equipment currently off; no idle energy accumulation.",
            "approval_required": False
        }
        
    # -------------------------------------------------------------
    # STEP 5: IDLE CONDITION IDENTIFICATION
    # -------------------------------------------------------------
    if p_active >= p_idle_threshold:
        trace.append({
            "step_number": 5,
            "step_name": "Idle Condition Identification",
            "status": "TERMINATED",
            "evaluation": f"Active power ({p_active} kW) >= P_idle threshold ({p_idle_threshold} kW). Active load present.",
            "values": {"p_active_kw": p_active, "p_idle_threshold_kw": p_idle_threshold}
        })
        return {
            "evaluation_step": 5,
            "outcome": DecisionOutcome.ACTIVELY_REQUIRED,
            "reason": f"Active power {p_active} kW >= idle threshold {p_idle_threshold} kW. Actively required in production.",
            "decision_trace": trace,
            "recommendation_text": "Normal production duty; continue continuous monitoring.",
            "approval_required": False
        }
        
    trace.append({
        "step_number": 5,
        "step_name": "Idle Condition Identification",
        "status": "PASSED",
        "evaluation": f"Low active power signature detected: P ({p_active} kW) < P_idle ({p_idle_threshold} kW).",
        "values": {"p_active_kw": p_active, "p_idle_threshold_kw": p_idle_threshold}
    })
    
    # -------------------------------------------------------------
    # STEP 6: IDLE DURATION VERIFICATION
    # -------------------------------------------------------------
    t_delay = getattr(equipment, "t_delay_seconds", 120.0)
    if idle_continuous_seconds < t_delay:
        trace.append({
            "step_number": 6,
            "step_name": "Idle Duration Verification",
            "status": "TERMINATED",
            "evaluation": f"Idle duration ({idle_continuous_seconds:.1f} s) < configured time delay ({t_delay} s). Transient idle.",
            "values": {"idle_continuous_seconds": idle_continuous_seconds, "t_delay_seconds": t_delay}
        })
        return {
            "evaluation_step": 6,
            "outcome": DecisionOutcome.ACTIVELY_REQUIRED,
            "reason": f"Idle duration {idle_continuous_seconds:.0f}s has not exceeded delay {t_delay:.0f}s. Awaiting qualification.",
            "decision_trace": trace,
            "recommendation_text": "Transient idle period; keep monitoring until duration qualifies.",
            "approval_required": False
        }
        
    trace.append({
        "step_number": 6,
        "step_name": "Idle Duration Verification",
        "status": "PASSED",
        "evaluation": f"Sustained idle verified: continuous duration ({idle_continuous_seconds:.1f} s) >= t_delay ({t_delay} s).",
        "values": {"idle_continuous_seconds": idle_continuous_seconds, "t_delay_seconds": t_delay}
    })
    
    # -------------------------------------------------------------
    # STEP 7: CHECK EQUIPMENT ELIGIBILITY & SAFETY INTERLOCKS
    # -------------------------------------------------------------
    criticality = getattr(equipment, "criticality", EquipmentCriticality.NON_CRITICAL)
    if criticality == EquipmentCriticality.CRITICAL or str(criticality).upper() == "CRITICAL":
        trace.append({
            "step_number": 7,
            "step_name": "Check Equipment Eligibility & Safety Interlocks",
            "status": "FAILED",
            "evaluation": "Equipment is classified as CRITICAL (e.g., process safety / cooling). Permanent automated control exclusion enforced.",
            "values": {"criticality": "CRITICAL", "eligible_for_shutdown": False}
        })
        return {
            "evaluation_step": 7,
            "outcome": DecisionOutcome.BLOCKED_CRITICAL,
            "reason": "Stopped at Step 7: Critical load — permanent automated shutdown exclusion enforced.",
            "decision_trace": trace,
            "recommendation_text": "Investigate process schedule upstream. Automated shutdown forbidden for critical services.",
            "approval_required": False
        }
        
    is_eligible = getattr(equipment, "eligible_for_shutdown", True)
    if not is_eligible:
        trace.append({
            "step_number": 7,
            "step_name": "Check Equipment Eligibility & Safety Interlocks",
            "status": "FAILED",
            "evaluation": "Equipment is marked ineligible for controlled shutdown in site configuration.",
            "values": {"eligible_for_shutdown": False}
        })
        return {
            "evaluation_step": 7,
            "outcome": DecisionOutcome.SUSTAINED_IDLE,
            "reason": "Stopped at Step 7: Equipment marked ineligible for automated shutdown.",
            "decision_trace": trace,
            "recommendation_text": "Review equipment eligibility setting in configuration.",
            "approval_required": False
        }
        
    # Check simulated interlock inputs
    estop = telemetry_sample.get("interlock_estop", False)
    overload = telemetry_sample.get("interlock_overload", False)
    permissive = telemetry_sample.get("interlock_process_permissive", True)
    manual_ovr = telemetry_sample.get("interlock_manual_override", False)
    
    interlock_blocks = []
    if estop:
        interlock_blocks.append("Emergency Stop circuit engaged")
    if overload:
        interlock_blocks.append("Motor thermal overload trip active")
    if not permissive:
        interlock_blocks.append("Upstream process permissive missing")
    if manual_ovr:
        interlock_blocks.append("Local manual maintenance override active")
        
    if interlock_blocks:
        trace.append({
            "step_number": 7,
            "step_name": "Check Equipment Eligibility & Safety Interlocks",
            "status": "FAILED",
            "evaluation": f"Simulated interlocks active: {'; '.join(interlock_blocks)}. Controlled shutdown blocked.",
            "values": {
                "estop": estop, "overload": overload, "process_permissive": permissive, "manual_override": manual_ovr
            }
        })
        return {
            "evaluation_step": 7,
            "outcome": DecisionOutcome.BLOCKED_INTERLOCK,
            "reason": f"Interlock active: {'; '.join(interlock_blocks)}. Shutdown inhibited.",
            "decision_trace": trace,
            "recommendation_text": "Clear safety interlocks and verify line safety before re-evaluating.",
            "approval_required": False
        }
        
    # Safe-restart protection checks
    max_restarts = getattr(equipment, "max_restarts_per_hour", 4)
    if recent_restarts_in_hour >= max_restarts:
        trace.append({
            "step_number": 7,
            "step_name": "Safe-Restart Protection Check",
            "status": "FAILED",
            "evaluation": f"Maximum restarts per hour reached ({recent_restarts_in_hour}/{max_restarts}). Thermal cycling protection active.",
            "values": {"recent_restarts": recent_restarts_in_hour, "max_restarts_per_hour": max_restarts}
        })
        return {
            "evaluation_step": 7,
            "outcome": DecisionOutcome.BLOCKED_RESTART_PROTECTION,
            "reason": f"Restart frequency limit reached ({recent_restarts_in_hour}/{max_restarts} restarts/hr). Motor thermal protection.",
            "decision_trace": trace,
            "recommendation_text": "Do not shut down if frequent restart is imminent to prevent motor winding heating.",
            "approval_required": False
        }
        
    trace.append({
        "step_number": 7,
        "step_name": "Check Equipment Eligibility & Safety Interlocks",
        "status": "PASSED",
        "evaluation": "Non-critical load confirmed. All safety interlocks permissive and restart limits verified.",
        "values": {
            "criticality": "NON_CRITICAL",
            "eligible_for_shutdown": True,
            "estop": False,
            "overload": False,
            "process_permissive": True,
            "manual_override": False
        }
    })
    
    # -------------------------------------------------------------
    # STEP 8: DECISION
    # -------------------------------------------------------------
    is_approved = operator_approval and getattr(operator_approval, "status", "") == "APPROVED"
    
    if is_approved:
        trace.append({
            "step_number": 8,
            "step_name": "Decision & Controlled Shutdown",
            "status": "PASSED",
            "evaluation": "Operator approval recorded. Initiating simulated controlled shutdown via contactor/VFD adapter.",
            "values": {
                "decision": DecisionOutcome.APPROVED_NON_CRITICAL.value,
                "approved_by": getattr(operator_approval, "reviewed_by", "OPERATOR"),
                "command_interface": "SIMULATED_CONTACTOR_VFD"
            }
        })
        return {
            "evaluation_step": 8,
            "outcome": DecisionOutcome.APPROVED_NON_CRITICAL,
            "reason": f"Sustained idle verified and approved by {getattr(operator_approval, 'reviewed_by', 'Operator')}. Executing simulated shutdown.",
            "decision_trace": trace,
            "recommendation_text": "Controlled shutdown initiated on simulated contactor/VFD adapter. Monitor line status.",
            "approval_required": False
        }
    else:
        trace.append({
            "step_number": 8,
            "step_name": "Decision & Operator Approval Requirement",
            "status": "PASSED",
            "evaluation": "Sustained idle verified. Energy-saving recommendation generated. Awaiting authorized operator approval.",
            "values": {
                "decision": DecisionOutcome.SUSTAINED_IDLE.value,
                "approval_required": True,
                "avoidable_kw": p_active
            }
        })
        return {
            "evaluation_step": 8,
            "outcome": DecisionOutcome.SUSTAINED_IDLE,
            "reason": f"Sustained idle of {idle_continuous_seconds:.0f}s on eligible equipment. Energy-saving recommendation generated.",
            "decision_trace": trace,
            "recommendation_text": "Request operator approval for simulated controlled shutdown to eliminate avoidable idle electricity.",
            "approval_required": True
        }
