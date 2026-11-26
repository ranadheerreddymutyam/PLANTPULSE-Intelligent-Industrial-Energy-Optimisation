"""Pydantic v2 Schemas for PlantPulse."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.core.provenance import (
    ProvenanceType, UserRole, EquipmentCriticality, OperatingState, DecisionOutcome, EventSeverity, EngineeringValue
)

class SiteConfigSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    site_name: str
    description: Optional[str] = None
    nominal_voltage_v: float
    nominal_frequency_hz: float
    voltage_min_v: float
    voltage_max_v: float
    frequency_min_hz: float
    frequency_max_hz: float
    power_factor_min: float
    tariff_per_kwh: float
    currency: str
    emission_factor_kg_co2_per_kwh: float
    restart_allowance_kwh: float
    alert_debounce_count: int
    alert_hysteresis_seconds: int
    config_version: str
    provenance: ProvenanceType
    updated_at: Optional[datetime] = None

class SiteConfigUpdate(BaseModel):
    site_name: Optional[str] = None
    nominal_voltage_v: Optional[float] = None
    nominal_frequency_hz: Optional[float] = None
    voltage_min_v: Optional[float] = None
    voltage_max_v: Optional[float] = None
    frequency_min_hz: Optional[float] = None
    frequency_max_hz: Optional[float] = None
    power_factor_min: Optional[float] = None
    tariff_per_kwh: Optional[float] = None
    currency: Optional[str] = None
    emission_factor_kg_co2_per_kwh: Optional[float] = None
    restart_allowance_kwh: Optional[float] = None
    alert_debounce_count: Optional[int] = None
    alert_hysteresis_seconds: Optional[int] = None

class EquipmentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    site_id: str
    name: str
    equipment_type: str
    rated_power_kw: float
    rated_current_a: float
    p_idle_threshold_kw: float
    t_delay_seconds: float
    criticality: EquipmentCriticality
    eligible_for_shutdown: bool
    vfd_capable: bool
    min_off_time_seconds: int
    restart_delay_seconds: int
    max_restarts_per_hour: int
    provenance: ProvenanceType
    config_version: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class EquipmentUpdate(BaseModel):
    name: Optional[str] = None
    equipment_type: Optional[str] = None
    p_idle_threshold_kw: Optional[float] = None
    t_delay_seconds: Optional[float] = None
    criticality: Optional[EquipmentCriticality] = None
    eligible_for_shutdown: Optional[bool] = None # Will still be strictly blocked if criticality is CRITICAL
    vfd_capable: Optional[bool] = None
    min_off_time_seconds: Optional[int] = None
    restart_delay_seconds: Optional[int] = None
    max_restarts_per_hour: Optional[int] = None

class TelemetrySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    equipment_id: str
    scenario_id: Optional[str] = None
    timestamp: datetime
    timestamp_epoch_s: float
    voltage_v: float
    current_a: float
    power_factor: float
    frequency_hz: float
    active_power_kw: float
    apparent_power_kva: float
    reactive_power_kvar: float
    cumulative_energy_kwh: float
    operating_state: OperatingState
    interlock_estop: bool
    interlock_overload: bool
    interlock_process_permissive: bool
    interlock_manual_override: bool
    provenance: ProvenanceType

class IdlePeriodSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    equipment_id: str
    scenario_id: Optional[str] = None
    start_time: datetime
    end_time: datetime
    start_epoch_s: float
    end_epoch_s: float
    duration_seconds: float
    p_idle_threshold_kw: float
    t_delay_seconds: float
    total_idle_energy_kwh: float
    avoidable_energy_kwh: float
    eligible: bool
    provenance: ProvenanceType
    created_at: Optional[datetime] = None

class DecisionTraceStep(BaseModel):
    step_number: int
    step_name: str
    status: str # PASSED, FAILED, SKIPPED, TERMINATED
    evaluation: str
    values: Dict[str, Any]

class DecisionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    equipment_id: str
    scenario_id: Optional[str] = None
    timestamp: datetime
    evaluation_step: int
    outcome: DecisionOutcome
    reason: str
    decision_trace: List[Dict[str, Any]]
    recommendation_text: Optional[str] = None
    approval_required: bool
    approval_id: Optional[int] = None
    provenance: ProvenanceType

class ApprovalSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    equipment_id: str
    scenario_id: Optional[str] = None
    action_type: str
    status: str
    requested_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    user_role: Optional[UserRole] = None
    comment: Optional[str] = None
    estimated_kwh_saving: float
    provenance: ProvenanceType

class ApprovalActionRequest(BaseModel):
    action: str # APPROVE or REJECT
    user_id: str
    user_role: UserRole
    comment: Optional[str] = None

class SimulatedCommandRequest(BaseModel):
    equipment_id: str
    command_type: str # SIMULATED_SHUTDOWN or SIMULATED_RESTART or MANUAL_OVERRIDE
    user_id: str
    user_role: UserRole
    reason: Optional[str] = None

class ControlCommandSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    equipment_id: str
    approval_id: Optional[int] = None
    command_type: str
    target_interface: str
    simulated_command_label: str
    status: str
    issued_by: str
    issued_at: datetime
    completed_at: datetime
    details: Optional[Dict[str, Any]] = None
    provenance: ProvenanceType

class EventSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    event_uid: str
    equipment_id: str
    scenario_id: Optional[str] = None
    severity: EventSeverity
    event_code: str
    parameter: str
    observed_value: Optional[float] = None
    threshold_reference: Optional[float] = None
    deviation: Optional[float] = None
    unit: str
    engineering_explanation: str
    recommended_consideration: str
    status: str
    occurrence_count: int
    started_at: datetime
    last_detected_at: datetime
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    provenance: ProvenanceType

class EventActionRequest(BaseModel):
    action: str # ACKNOWLEDGE or RESOLVE
    user_id: str

class ScenarioSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    description: str
    seed: int
    duration_hours: float
    is_active: bool
    generated_at: datetime
    provenance: ProvenanceType

class ScenarioSwitchRequest(BaseModel):
    scenario_id: str

class BaselineComparisonSchema(BaseModel):
    baseline_run_id: int
    optimised_run_id: int
    scenario_id: str
    seed: int
    baseline_kwh: float
    optimised_kwh: float
    saved_kwh: float
    saving_percentage: float
    cost_saved: float
    emissions_saved_kg_co2: float
    currency: str
    assumptions: Dict[str, Any]
    provenance: ProvenanceType

class ImportSummarySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    filename: str
    file_type: str
    record_count: int
    valid_count: int
    warning_count: int
    error_count: int
    summary: Dict[str, Any]
    schema_version: str
    provenance: ProvenanceType
    imported_at: datetime

class ReportSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    report_type: str
    scenario_id: Optional[str] = None
    generated_at: datetime
    data: Dict[str, Any]
    provenance: ProvenanceType
    model_version: str

class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    username: str
    full_name: str
    role: UserRole
    is_active: bool

class UserLoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserSchema

class AuditLogSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    timestamp: datetime
    user_id: str
    role: str
    action: str
    entity: str
    entity_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    provenance: ProvenanceType
