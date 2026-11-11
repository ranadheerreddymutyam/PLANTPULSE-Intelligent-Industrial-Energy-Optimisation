"""Unit tests for the Centralized Engineering Calculation Layer."""
import pytest
import math
from app.engineering.calculations import (
    compute_apparent_power,
    compute_active_power,
    compute_power_factor,
    compute_reactive_power,
    integrate_energy_trapezoidal,
    is_idle_sample,
    evaluate_idle_periods,
    compute_idle_share,
    compute_estimated_savings,
    compute_before_after_saving_percentage,
    SQRT3,
)
from app.core.provenance import ProvenanceType

def test_apparent_power_hand_computed():
    # V = 415 V, I = 100 A
    # S = sqrt(3) * 415 * 100 / 1000 = 1.7320508 * 41.5 = 71.8795 kVA
    res = compute_apparent_power(415.0, 100.0)
    assert res.unit == "kVA"
    assert res.provenance == ProvenanceType.DERIVED
    expected = round((math.sqrt(3.0) * 415.0 * 100.0) / 1000.0, 4)
    assert res.value == expected
    assert abs(res.value - 71.8801) < 0.01

def test_apparent_power_edge_cases():
    # Zero current
    res_zero = compute_apparent_power(415.0, 0.0)
    assert res_zero.value == 0.0
    
    # Negative values guard
    res_neg = compute_apparent_power(-415.0, 50.0)
    assert res_neg.value == 0.0

def test_active_power():
    # V = 415 V, I = 100 A, PF = 0.85
    # P = sqrt(3) * 415 * 100 * 0.85 / 1000 = 61.0981 kW
    res = compute_active_power(415.0, 100.0, 0.85)
    assert res.unit == "kW"
    assert abs(res.value - 61.0981) < 0.01
    
    # Metered direct override
    res_metered = compute_active_power(415.0, 100.0, 0.85, metered_kw=42.5)
    assert res_metered.value == 42.5
    assert res_metered.provenance == ProvenanceType.IMPORTED

def test_power_factor_and_reactive_power():
    # S = 100 kVA, P = 80 kW -> PF = 0.80, Q = sqrt(100^2 - 80^2) = 60 kvar
    pf_res = compute_power_factor(80.0, 100.0)
    assert pf_res.value == 0.80
    
    q_res = compute_reactive_power(100.0, 80.0)
    assert q_res.value == 60.0
    assert q_res.unit == "kvar"
    
    # S = 0 guard
    pf_zero = compute_power_factor(0.0, 0.0)
    assert pf_zero.value == 0.0

def test_energy_trapezoidal_integration():
    # Timestamps every 3600 seconds (1 hour): [0, 3600, 7200]
    # Powers: [10 kW, 10 kW, 20 kW]
    # Segment 1: 0.5 * (10 + 10) * (3600/3600) = 10 kWh
    # Segment 2: 0.5 * (10 + 20) * (3600/3600) = 15 kWh
    # Total = 25 kWh
    t = [0.0, 3600.0, 7200.0]
    p = [10.0, 10.0, 20.0]
    res = integrate_energy_trapezoidal(t, p)
    assert res.value == 25.0
    assert res.unit == "kWh"

def test_energy_trapezoidal_non_monotonic_guard():
    # Non-monotonic or negative dt should be safely skipped
    t = [0.0, 3600.0, 3600.0, 1800.0, 7200.0]
    p = [10.0, 10.0, 10.0, 10.0, 20.0]
    res = integrate_energy_trapezoidal(t, p)
    # Valid segments: 0->3600 (10 kWh), then 1800->7200 (dt=5400s=1.5h, avg=15kW -> 22.5 kWh)
    assert res.value > 0

def test_idle_condition_and_state():
    # P < P_idle while RUNNING -> True
    assert is_idle_sample(4.5, 5.0, "RUNNING") is True
    # P >= P_idle -> False
    assert is_idle_sample(5.5, 5.0, "RUNNING") is False
    # STOPPED state -> False even if P=0
    assert is_idle_sample(0.0, 5.0, "STOPPED") is False

def test_idle_periods_duration_and_avoidable():
    # 5 samples, 60s apart: 0, 60, 120, 180, 240 (total span 240s)
    # Power = 4.0 kW throughout (idle threshold = 5.0 kW)
    t = [0.0, 60.0, 120.0, 180.0, 240.0]
    p = [4.0, 4.0, 4.0, 4.0, 4.0]
    states = ["RUNNING"] * 5
    
    # Case A: t_delay = 120s, eligible = True
    # Total idle period = 240s >= 120s -> 1 qualifying period
    # Total idle energy = 4 kW * (240/3600) = 0.2667 kWh
    # Portion after 120s: from t=120 to t=240 (120s = 0.0333h) -> 4 * (120/3600) = 0.1333 kWh avoidable
    res_eligible = evaluate_idle_periods(t, p, states, p_idle_threshold_kw=5.0, t_delay_seconds=120.0, is_eligible=True)
    assert res_eligible["qualifying_period_count"] == 1
    assert abs(res_eligible["total_idle_energy_kwh"].value - 0.2667) < 0.001
    assert abs(res_eligible["avoidable_idle_energy_kwh"].value - 0.1333) < 0.001
    
    # Case B: eligible = False (e.g. Critical Load) -> Avoidable MUST BE ZERO
    res_ineligible = evaluate_idle_periods(t, p, states, p_idle_threshold_kw=5.0, t_delay_seconds=120.0, is_eligible=False)
    assert res_ineligible["qualifying_period_count"] == 1
    assert res_ineligible["avoidable_idle_energy_kwh"].value == 0.0

    # Case C: t_delay = 300s (longer than 240s) -> Must NOT qualify
    res_short = evaluate_idle_periods(t, p, states, p_idle_threshold_kw=5.0, t_delay_seconds=300.0, is_eligible=True)
    assert res_short["qualifying_period_count"] == 0
    assert res_short["total_idle_energy_kwh"].value == 0.0
    assert res_short["avoidable_idle_energy_kwh"].value == 0.0

def test_estimated_savings_and_before_after():
    avoidable_kwh = 100.0
    savings = compute_estimated_savings(
        avoidable_idle_kwh=avoidable_kwh,
        restart_allowance_kwh=5.0,
        tariff_per_kwh=0.20,
        emission_factor_kg_co2_per_kwh=0.50,
        currency="USD"
    )
    # E_save = 100 - 5 = 95 kWh
    assert savings["energy_savings_kwh"].value == 95.0
    # Cost = 95 * 0.20 = 19.00 USD
    assert savings["cost_savings"].value == 19.0
    assert savings["cost_savings"].unit == "USD"
    # CO2 = 95 * 0.50 = 47.5 kg CO2e
    assert savings["emissions_reduction_kg_co2"].value == 47.5

    # Before / After saving %
    pct = compute_before_after_saving_percentage(baseline_kwh=1000.0, after_kwh=900.0)
    assert pct.value == 10.0
    assert pct.unit == "%"
