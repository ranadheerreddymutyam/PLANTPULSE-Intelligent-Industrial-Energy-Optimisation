"""Unit tests for the 8-Step Logical Flow State Machine."""
import pytest
from app.services.logical_flow import evaluate_logical_flow
from app.core.provenance import DecisionOutcome, EquipmentCriticality, OperatingState

class MockEquipment:
    def __init__(
        self,
        id="eq_test",
        rated_power_kw=30.0,
        rated_current_a=52.0,
        p_idle_threshold_kw=7.0,
        t_delay_seconds=120.0,
        criticality=EquipmentCriticality.NON_CRITICAL,
        eligible_for_shutdown=True,
        max_restarts_per_hour=4
    ):
        self.id = id
        self.rated_power_kw = rated_power_kw
        self.rated_current_a = rated_current_a
        self.p_idle_threshold_kw = p_idle_threshold_kw
        self.t_delay_seconds = t_delay_seconds
        self.criticality = criticality
        self.eligible_for_shutdown = eligible_for_shutdown
        self.max_restarts_per_hour = max_restarts_per_hour

class MockSiteConfig:
    voltage_min_v = 373.5
    voltage_max_v = 456.5
    frequency_min_hz = 47.5
    frequency_max_hz = 52.5

class MockApproval:
    def __init__(self, status="APPROVED", reviewed_by="Operator Alice"):
        self.status = status
        self.reviewed_by = reviewed_by

def test_step_2_rejection_voltage_fault():
    eq = MockEquipment()
    site = MockSiteConfig()
    # Voltage = 500 V (> 456.5 V)
    telemetry = {
        "voltage_v": 500.0,
        "current_a": 10.0,
        "frequency_hz": 50.0,
        "power_factor": 0.85
    }
    result = evaluate_logical_flow(eq, site, telemetry)
    assert result["evaluation_step"] == 2
    assert result["outcome"] == DecisionOutcome.REJECTED_INPUT_FAULT
    assert "Voltage 500.0 V outside allowable range" in result["reason"]

def test_step_4_stopped_state():
    eq = MockEquipment()
    site = MockSiteConfig()
    # Current < 0.05 * 52 A = 2.6 A
    telemetry = {
        "voltage_v": 415.0,
        "current_a": 1.0,
        "frequency_hz": 50.0,
        "power_factor": 0.2,
        "operating_state": "STOPPED"
    }
    result = evaluate_logical_flow(eq, site, telemetry)
    assert result["evaluation_step"] == 4
    assert result["outcome"] == DecisionOutcome.ACTIVELY_REQUIRED
    assert "stopped" in result["reason"].lower()

def test_step_5_normal_production_load():
    eq = MockEquipment() # rated 30 kW, p_idle = 7 kW
    site = MockSiteConfig()
    # P = 25 kW >= 7 kW
    telemetry = {
        "voltage_v": 415.0,
        "current_a": 42.0,
        "frequency_hz": 50.0,
        "power_factor": 0.85,
        "active_power_kw": 25.0
    }
    result = evaluate_logical_flow(eq, site, telemetry)
    assert result["evaluation_step"] == 5
    assert result["outcome"] == DecisionOutcome.ACTIVELY_REQUIRED
    assert "actively required" in result["reason"].lower()

def test_step_6_transient_short_idle():
    eq = MockEquipment(t_delay_seconds=120.0)
    site = MockSiteConfig()
    # P = 4 kW (< 7 kW), but idle duration = 60s (< 120s)
    telemetry = {
        "voltage_v": 415.0,
        "current_a": 12.0,
        "frequency_hz": 50.0,
        "power_factor": 0.35,
        "active_power_kw": 4.0
    }
    result = evaluate_logical_flow(eq, site, telemetry, idle_continuous_seconds=60.0)
    assert result["evaluation_step"] == 6
    assert result["outcome"] == DecisionOutcome.ACTIVELY_REQUIRED
    assert "awaiting qualification" in result["reason"].lower()

def test_step_7_critical_load_permanent_exclusion():
    # Main Process Motor or Cooling Water Pump (CRITICAL)
    eq = MockEquipment(criticality=EquipmentCriticality.CRITICAL, eligible_for_shutdown=False)
    site = MockSiteConfig()
    telemetry = {
        "voltage_v": 415.0,
        "current_a": 12.0,
        "frequency_hz": 50.0,
        "power_factor": 0.35,
        "active_power_kw": 4.0
    }
    result = evaluate_logical_flow(eq, site, telemetry, idle_continuous_seconds=300.0)
    assert result["evaluation_step"] == 7
    assert result["outcome"] == DecisionOutcome.BLOCKED_CRITICAL
    assert "critical load" in result["reason"].lower()
    assert result["approval_required"] is False

def test_step_7_interlock_blocked():
    eq = MockEquipment()
    site = MockSiteConfig()
    # E-Stop engaged
    telemetry = {
        "voltage_v": 415.0,
        "current_a": 12.0,
        "frequency_hz": 50.0,
        "power_factor": 0.35,
        "active_power_kw": 4.0,
        "interlock_estop": True
    }
    result = evaluate_logical_flow(eq, site, telemetry, idle_continuous_seconds=300.0)
    assert result["evaluation_step"] == 7
    assert result["outcome"] == DecisionOutcome.BLOCKED_INTERLOCK
    assert "Emergency Stop" in result["reason"]

def test_step_7_restart_protection_limit():
    eq = MockEquipment(max_restarts_per_hour=3)
    site = MockSiteConfig()
    telemetry = {
        "voltage_v": 415.0,
        "current_a": 12.0,
        "frequency_hz": 50.0,
        "power_factor": 0.35,
        "active_power_kw": 4.0
    }
    result = evaluate_logical_flow(eq, site, telemetry, idle_continuous_seconds=300.0, recent_restarts_in_hour=3)
    assert result["evaluation_step"] == 7
    assert result["outcome"] == DecisionOutcome.BLOCKED_RESTART_PROTECTION

def test_step_8_sustained_idle_awaiting_approval():
    eq = MockEquipment()
    site = MockSiteConfig()
    telemetry = {
        "voltage_v": 415.0,
        "current_a": 12.0,
        "frequency_hz": 50.0,
        "power_factor": 0.35,
        "active_power_kw": 4.0
    }
    result = evaluate_logical_flow(eq, site, telemetry, idle_continuous_seconds=300.0, operator_approval=None)
    assert result["evaluation_step"] == 8
    assert result["outcome"] == DecisionOutcome.SUSTAINED_IDLE
    assert result["approval_required"] is True

def test_step_8_approved_controlled_shutdown():
    eq = MockEquipment()
    site = MockSiteConfig()
    telemetry = {
        "voltage_v": 415.0,
        "current_a": 12.0,
        "frequency_hz": 50.0,
        "power_factor": 0.35,
        "active_power_kw": 4.0
    }
    approval = MockApproval(status="APPROVED", reviewed_by="Operator Bob")
    result = evaluate_logical_flow(eq, site, telemetry, idle_continuous_seconds=300.0, operator_approval=approval)
    assert result["evaluation_step"] == 8
    assert result["outcome"] == DecisionOutcome.APPROVED_NON_CRITICAL
    assert "Bob" in result["reason"]
