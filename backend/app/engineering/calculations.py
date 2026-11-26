"""Centralized Engineering Calculation Layer for PlantPulse.

Strictly non-AI, non-ML, pure physical/electrical engineering equations.
All 3-phase AC calculations assume balanced 3-phase load (V = Line-to-Line RMS, I = Line RMS).
"""
import math
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from app.core.provenance import ProvenanceType, EngineeringValue
from app.core.config import settings

SQRT3 = math.sqrt(3.0)  # 1.7320508075688772

def compute_apparent_power(
    voltage_v: float,
    current_a: float,
    model_version: str = settings.MODEL_VERSION,
    provenance: ProvenanceType = ProvenanceType.DERIVED
) -> EngineeringValue:
    """Computes 3-phase apparent power S = sqrt(3) * V_LL * I / 1000 [kVA]."""
    if voltage_v is None or current_a is None or voltage_v < 0 or current_a < 0:
        val = 0.0
    else:
        val = round((SQRT3 * voltage_v * current_a) / 1000.0, 4)
        
    return EngineeringValue(
        value=val,
        unit="kVA",
        formula="S = sqrt(3) * V_LL * I / 1000",
        inputs={"voltage_v": voltage_v, "current_a": current_a},
        provenance=provenance,
        model_version=model_version,
        note="Balanced 3-phase AC assumption, Line-to-Line RMS voltage"
    )

def compute_active_power(
    voltage_v: float,
    current_a: float,
    power_factor: float,
    metered_kw: Optional[float] = None,
    model_version: str = settings.MODEL_VERSION,
    provenance: Optional[ProvenanceType] = None
) -> EngineeringValue:
    """Computes active power P = sqrt(3) * V_LL * I * PF / 1000 [kW] or uses metered_kw if provided."""
    if metered_kw is not None and not math.isnan(metered_kw):
        return EngineeringValue(
            value=round(float(metered_kw), 4),
            unit="kW",
            formula="P = metered_kw (direct measurement/import)",
            inputs={"metered_kw": metered_kw},
            provenance=provenance or ProvenanceType.IMPORTED,
            model_version=model_version
        )
    
    if voltage_v is None or current_a is None or power_factor is None or voltage_v < 0 or current_a < 0:
        val = 0.0
    else:
        clamped_pf = max(0.0, min(1.0, power_factor))
        val = round((SQRT3 * voltage_v * current_a * clamped_pf) / 1000.0, 4)
        
    return EngineeringValue(
        value=val,
        unit="kW",
        formula="P = sqrt(3) * V_LL * I * PF / 1000",
        inputs={"voltage_v": voltage_v, "current_a": current_a, "power_factor": power_factor},
        provenance=provenance or ProvenanceType.DERIVED,
        model_version=model_version,
        note="Balanced 3-phase AC active power"
    )

def compute_power_factor(
    active_power_kw: float,
    apparent_power_kva: float,
    model_version: str = settings.MODEL_VERSION,
    provenance: ProvenanceType = ProvenanceType.DERIVED
) -> EngineeringValue:
    """Computes Power Factor PF = P / S with S = 0 guard."""
    if apparent_power_kva is None or apparent_power_kva <= 1e-6:
        val = 1.0 if (active_power_kw is not None and active_power_kw > 0) else 0.0
    else:
        raw = active_power_kw / apparent_power_kva
        val = round(max(0.0, min(1.0, raw)), 4)
        
    return EngineeringValue(
        value=val,
        unit="dimensionless",
        formula="PF = P / S (guarded against S=0)",
        inputs={"active_power_kw": active_power_kw, "apparent_power_kva": apparent_power_kva},
        provenance=provenance,
        model_version=model_version
    )

def compute_reactive_power(
    apparent_power_kva: float,
    active_power_kw: float,
    model_version: str = settings.MODEL_VERSION,
    provenance: ProvenanceType = ProvenanceType.DERIVED
) -> EngineeringValue:
    """Computes Reactive Power Q = sqrt(max(0, S^2 - P^2)) [kvar]."""
    if apparent_power_kva is None or active_power_kw is None:
        val = 0.0
    else:
        s = max(0.0, apparent_power_kva)
        p = max(0.0, active_power_kw)
        diff = max(0.0, (s ** 2) - (p ** 2))
        val = round(math.sqrt(diff), 4)
        
    return EngineeringValue(
        value=val,
        unit="kvar",
        formula="Q = sqrt(max(0, S^2 - P^2))",
        inputs={"apparent_power_kva": apparent_power_kva, "active_power_kw": active_power_kw},
        provenance=provenance,
        model_version=model_version
    )

def integrate_energy_trapezoidal(
    timestamps_epoch_s: List[float],
    powers_kw: List[float],
    model_version: str = settings.MODEL_VERSION,
    provenance: ProvenanceType = ProvenanceType.DERIVED
) -> EngineeringValue:
    """Computes energy E = integral(P dt) using the trapezoidal rule over timestamps in hours."""
    if not timestamps_epoch_s or len(timestamps_epoch_s) < 2 or len(timestamps_epoch_s) != len(powers_kw):
        return EngineeringValue(
            value=0.0,
            unit="kWh",
            formula="E = sum(0.5 * (P[i-1] + P[i]) * dt / 3600)",
            inputs={"sample_count": len(timestamps_epoch_s) if timestamps_epoch_s else 0},
            provenance=provenance,
            model_version=model_version,
            note="Insufficient samples for integration (<2 samples)"
        )
    
    total_energy_kwh = 0.0
    invalid_dt_count = 0
    
    for i in range(1, len(timestamps_epoch_s)):
        t_prev = timestamps_epoch_s[i - 1]
        t_curr = timestamps_epoch_s[i]
        dt = t_curr - t_prev
        
        # Guard against non-monotonic or negative timestamps
        if dt <= 0:
            invalid_dt_count += 1
            continue
            
        p_prev = max(0.0, powers_kw[i - 1] if powers_kw[i - 1] is not None else 0.0)
        p_curr = max(0.0, powers_kw[i] if powers_kw[i] is not None else 0.0)
        
        # dt is in seconds, convert to hours: / 3600
        segment_energy = 0.5 * (p_prev + p_curr) * (dt / 3600.0)
        total_energy_kwh += segment_energy
        
    return EngineeringValue(
        value=round(total_energy_kwh, 4),
        unit="kWh",
        formula="E = integral(P dt) via trapezoidal integration",
        inputs={
            "sample_count": len(timestamps_epoch_s),
            "duration_hours": round((timestamps_epoch_s[-1] - timestamps_epoch_s[0]) / 3600.0, 4) if len(timestamps_epoch_s) > 1 else 0.0,
            "invalid_dt_skipped": invalid_dt_count
        },
        provenance=provenance,
        model_version=model_version
    )

def is_idle_sample(
    power_kw: float,
    p_idle_threshold_kw: float,
    operating_state: str
) -> bool:
    """Idle condition: idle(t) = (P < P_idle) AND state in ('RUNNING', 'IDLE') (not STOPPED)."""
    if power_kw is None or p_idle_threshold_kw is None:
        return False
    state_upper = (operating_state or "").upper()
    if state_upper in ("STOPPED", "STOP", "OFF", "SHUTDOWN"):
        return False
    return power_kw < p_idle_threshold_kw

def evaluate_idle_periods(
    timestamps_epoch_s: List[float],
    powers_kw: List[float],
    states: List[str],
    p_idle_threshold_kw: float,
    t_delay_seconds: float,
    is_eligible: bool,
    model_version: str = settings.MODEL_VERSION
) -> Dict[str, Any]:
    """Analyzes continuous telemetry series to detect qualifying idle periods and avoidable idle energy.
    
    Qualifying idle period: continuous idle where total_duration >= t_delay.
    Avoidable energy: integral of P dt strictly over the portion AFTER t_delay has elapsed,
    for eligible equipment only.
    """
    if not timestamps_epoch_s or len(timestamps_epoch_s) < 2:
        return {
            "periods": [],
            "total_idle_energy_kwh": EngineeringValue(
                value=0.0, unit="kWh", formula="E_idle = sum(E_period)",
                inputs={"qualifying_periods": 0}, provenance=ProvenanceType.DERIVED, model_version=model_version
            ),
            "avoidable_idle_energy_kwh": EngineeringValue(
                value=0.0, unit="kWh", formula="E_avoid = sum(E_period_after_delay) * is_eligible",
                inputs={"is_eligible": is_eligible, "qualifying_periods": 0}, provenance=ProvenanceType.ESTIMATED, model_version=model_version
            ),
            "total_idle_duration_seconds": 0.0,
            "qualifying_period_count": 0
        }
        
    periods = []
    current_period_t = []
    current_period_p = []
    
    for i in range(len(timestamps_epoch_s)):
        t = timestamps_epoch_s[i]
        p = powers_kw[i]
        st = states[i] if i < len(states) else "RUNNING"
        
        idle = is_idle_sample(p, p_idle_threshold_kw, st)
        
        if idle:
            current_period_t.append(t)
            current_period_p.append(p)
        else:
            # End of an idle segment
            if len(current_period_t) >= 2:
                duration_s = current_period_t[-1] - current_period_t[0]
                if duration_s >= t_delay_seconds:
                    periods.append((list(current_period_t), list(current_period_p), duration_s))
            current_period_t = []
            current_period_p = []
            
    # Check trailing period
    if len(current_period_t) >= 2:
        duration_s = current_period_t[-1] - current_period_t[0]
        if duration_s >= t_delay_seconds:
            periods.append((list(current_period_t), list(current_period_p), duration_s))
            
    total_idle_kwh = 0.0
    avoidable_kwh = 0.0
    total_qualifying_duration_s = 0.0
    structured_periods = []
    
    for idx, (p_t, p_p, dur_s) in enumerate(periods):
        total_qualifying_duration_s += dur_s
        # Total idle energy for this period
        period_e = integrate_energy_trapezoidal(p_t, p_p, model_version).value or 0.0
        total_idle_kwh += period_e
        
        # Avoidable portion: portion after t_start + t_delay
        t_start = p_t[0]
        t_cutoff = t_start + t_delay_seconds
        
        # Sub-slice after cutoff
        avoidable_t = []
        avoidable_p = []
        for j in range(len(p_t)):
            if p_t[j] >= t_cutoff:
                # If first point after cutoff, interpolate or include boundary
                if not avoidable_t and j > 0:
                    # boundary point at t_cutoff
                    t_prev, t_curr = p_t[j-1], p_t[j]
                    p_prev, p_curr = p_p[j-1], p_p[j]
                    fraction = (t_cutoff - t_prev) / (t_curr - t_prev) if t_curr > t_prev else 0.0
                    p_interp = p_prev + fraction * (p_curr - p_prev)
                    avoidable_t.append(t_cutoff)
                    avoidable_p.append(p_interp)
                avoidable_t.append(p_t[j])
                avoidable_p.append(p_p[j])
                
        period_avoidable_kwh = 0.0
        if len(avoidable_t) >= 2 and is_eligible:
            period_avoidable_kwh = integrate_energy_trapezoidal(avoidable_t, avoidable_p, model_version).value or 0.0
            avoidable_kwh += period_avoidable_kwh
            
        structured_periods.append({
            "period_index": idx + 1,
            "start_time_iso": datetime.fromtimestamp(t_start, tz=timezone.utc).isoformat(),
            "end_time_iso": datetime.fromtimestamp(p_t[-1], tz=timezone.utc).isoformat(),
            "duration_seconds": round(dur_s, 2),
            "idle_energy_kwh": round(period_e, 4),
            "avoidable_energy_kwh": round(period_avoidable_kwh if is_eligible else 0.0, 4),
            "eligible_for_shutdown": is_eligible,
            "t_delay_seconds": t_delay_seconds
        })
        
    return {
        "periods": structured_periods,
        "total_idle_energy_kwh": EngineeringValue(
            value=round(total_idle_kwh, 4),
            unit="kWh",
            formula="E_idle = sum(E_period) over qualifying periods (t >= t_delay)",
            inputs={"qualifying_period_count": len(periods), "t_delay_seconds": t_delay_seconds},
            provenance=ProvenanceType.DERIVED,
            model_version=model_version
        ),
        "avoidable_idle_energy_kwh": EngineeringValue(
            value=round(avoidable_kwh, 4) if is_eligible else 0.0,
            unit="kWh",
            formula="E_avoid = sum(integral(P dt) for t > t_start + t_delay) if eligible else 0",
            inputs={"qualifying_period_count": len(periods), "is_eligible": is_eligible, "t_delay_seconds": t_delay_seconds},
            provenance=ProvenanceType.ESTIMATED,
            model_version=model_version,
            note="Zero if equipment is critical or not flagged eligible"
        ),
        "total_idle_duration_seconds": round(total_qualifying_duration_s, 2),
        "qualifying_period_count": len(periods)
    }

def compute_idle_share(
    total_idle_energy_kwh: float,
    total_energy_kwh: float,
    model_version: str = settings.MODEL_VERSION
) -> EngineeringValue:
    """Computes Idle Share % = (E_idle / E_total) * 100 with guard against E_total = 0."""
    if total_energy_kwh is None or total_energy_kwh <= 1e-6:
        val = 0.0
    else:
        val = round(max(0.0, min(100.0, (total_idle_energy_kwh / total_energy_kwh) * 100.0)), 2)
        
    return EngineeringValue(
        value=val,
        unit="%",
        formula="Idle Share = (E_idle / E_total) * 100",
        inputs={"total_idle_energy_kwh": total_idle_energy_kwh, "total_energy_kwh": total_energy_kwh},
        provenance=ProvenanceType.DERIVED,
        model_version=model_version
    )

def compute_estimated_savings(
    avoidable_idle_kwh: float,
    restart_allowance_kwh: float = 0.0,
    tariff_per_kwh: float = settings.DEFAULT_TARIFF_PER_KWH,
    emission_factor_kg_co2_per_kwh: float = settings.DEFAULT_EMISSION_FACTOR_KG_CO2_PER_KWH,
    currency: str = settings.DEFAULT_CURRENCY,
    model_version: str = settings.MODEL_VERSION
) -> Dict[str, EngineeringValue]:
    """Computes Estimated Energy, Cost, and Carbon savings with explicit assumptions."""
    e_save = max(0.0, avoidable_idle_kwh - (restart_allowance_kwh or 0.0))
    cost_save = e_save * tariff_per_kwh
    emission_save = e_save * emission_factor_kg_co2_per_kwh
    
    return {
        "energy_savings_kwh": EngineeringValue(
            value=round(e_save, 4),
            unit="kWh",
            formula="E_save = max(0, E_avoid - E_restart_allowance)",
            inputs={"avoidable_idle_kwh": avoidable_idle_kwh, "restart_allowance_kwh": restart_allowance_kwh},
            provenance=ProvenanceType.ESTIMATED,
            model_version=model_version,
            note="Restart allowance is a configured engineering reference assumption"
        ),
        "cost_savings": EngineeringValue(
            value=round(cost_save, 2),
            unit=currency,
            formula="Cost Save = E_save * tariff",
            inputs={"e_save_kwh": round(e_save, 4), "tariff_per_kwh": tariff_per_kwh},
            provenance=ProvenanceType.ESTIMATED,
            model_version=model_version,
            note=f"Tariff reference rate: {tariff_per_kwh} {currency}/kWh"
        ),
        "emissions_reduction_kg_co2": EngineeringValue(
            value=round(emission_save, 3),
            unit="kg CO2e",
            formula="Emissions Reduction = E_save * emission_factor",
            inputs={"e_save_kwh": round(e_save, 4), "emission_factor_kg_co2_per_kwh": emission_factor_kg_co2_per_kwh},
            provenance=ProvenanceType.ESTIMATED,
            model_version=model_version,
            note="Demonstration reference emission factor; not an official regulatory figure"
        )
    }

def compute_before_after_saving_percentage(
    baseline_kwh: float,
    after_kwh: float,
    model_version: str = settings.MODEL_VERSION
) -> EngineeringValue:
    """Computes saving % = ((E_baseline - E_after) / E_baseline) * 100.
    Computed ONLY between two runs with identical seed, schedule and operating conditions.
    """
    if baseline_kwh is None or baseline_kwh <= 1e-6:
        val = 0.0
    else:
        val = round(((baseline_kwh - after_kwh) / baseline_kwh) * 100.0, 2)
        
    return EngineeringValue(
        value=val,
        unit="%",
        formula="Saving % = ((E_baseline - E_after) / E_baseline) * 100",
        inputs={"baseline_kwh": baseline_kwh, "after_kwh": after_kwh},
        provenance=ProvenanceType.DERIVED,
        model_version=model_version,
        note="Valid only for identical baseline and optimized operating conditions (same seed and load schedule)"
    )
