"""SQLAlchemy 2.0 Data Models for PlantPulse."""
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.provenance import (
    ProvenanceType, UserRole, EquipmentCriticality, OperatingState, DecisionOutcome, EventSeverity
)

def utcnow():
    return datetime.now(timezone.utc)

class SiteConfig(Base):
    __tablename__ = "site_config"
    
    id = Column(String(50), primary_key=True)
    site_name = Column(String(100), nullable=False)
    description = Column(String(255))
    nominal_voltage_v = Column(Float, default=415.0)
    nominal_frequency_hz = Column(Float, default=50.0)
    voltage_min_v = Column(Float, default=373.5)
    voltage_max_v = Column(Float, default=456.5)
    frequency_min_hz = Column(Float, default=47.5)
    frequency_max_hz = Column(Float, default=52.5)
    power_factor_min = Column(Float, default=0.80)
    tariff_per_kwh = Column(Float, default=0.18)
    currency = Column(String(10), default="USD")
    emission_factor_kg_co2_per_kwh = Column(Float, default=0.42)
    restart_allowance_kwh = Column(Float, default=0.0)
    alert_debounce_count = Column(Integer, default=3)
    alert_hysteresis_seconds = Column(Integer, default=300)
    config_version = Column(String(20), default="1.0.0")
    provenance = Column(SQLEnum(ProvenanceType), default=ProvenanceType.CONFIGURED)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

class Equipment(Base):
    __tablename__ = "equipment"
    
    id = Column(String(50), primary_key=True)
    site_id = Column(String(50), ForeignKey("site_config.id"), nullable=False)
    name = Column(String(100), nullable=False)
    equipment_type = Column(String(50), nullable=False) # motor, pump, fan, auxiliary
    rated_power_kw = Column(Float, nullable=False)
    rated_current_a = Column(Float, nullable=False)
    p_idle_threshold_kw = Column(Float, nullable=False)
    t_delay_seconds = Column(Float, nullable=False)
    criticality = Column(SQLEnum(EquipmentCriticality), default=EquipmentCriticality.NON_CRITICAL)
    eligible_for_shutdown = Column(Boolean, default=True) # Derived/enforced: if CRITICAL, MUST be False
    vfd_capable = Column(Boolean, default=False)
    min_off_time_seconds = Column(Integer, default=180)
    restart_delay_seconds = Column(Integer, default=60)
    max_restarts_per_hour = Column(Integer, default=4)
    provenance = Column(SQLEnum(ProvenanceType), default=ProvenanceType.CONFIGURED)
    config_version = Column(String(20), default="1.0.0")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    
    telemetry_records = relationship("Telemetry", back_populates="equipment", cascade="all, delete-orphan")
    idle_periods = relationship("IdlePeriod", back_populates="equipment", cascade="all, delete-orphan")
    decisions = relationship("Decision", back_populates="equipment", cascade="all, delete-orphan")
    control_commands = relationship("ControlCommand", back_populates="equipment", cascade="all, delete-orphan")

class Telemetry(Base):
    __tablename__ = "telemetry"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    equipment_id = Column(String(50), ForeignKey("equipment.id"), nullable=False, index=True)
    scenario_id = Column(String(50), index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    timestamp_epoch_s = Column(Float, nullable=False)
    voltage_v = Column(Float, nullable=False)
    current_a = Column(Float, nullable=False)
    power_factor = Column(Float, nullable=False)
    frequency_hz = Column(Float, default=50.0)
    active_power_kw = Column(Float, nullable=False)
    apparent_power_kva = Column(Float, nullable=False)
    reactive_power_kvar = Column(Float, nullable=False)
    cumulative_energy_kwh = Column(Float, default=0.0)
    operating_state = Column(SQLEnum(OperatingState), default=OperatingState.RUNNING)
    
    # Interlocks state
    interlock_estop = Column(Boolean, default=False)
    interlock_overload = Column(Boolean, default=False)
    interlock_process_permissive = Column(Boolean, default=True)
    interlock_manual_override = Column(Boolean, default=False)
    
    provenance = Column(SQLEnum(ProvenanceType), default=ProvenanceType.SIMULATED)
    model_version = Column(String(20), default="1.0.0-prototype")
    
    equipment = relationship("Equipment", back_populates="telemetry_records")

class IdlePeriod(Base):
    __tablename__ = "idle_periods"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    equipment_id = Column(String(50), ForeignKey("equipment.id"), nullable=False, index=True)
    scenario_id = Column(String(50), index=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    start_epoch_s = Column(Float, nullable=False)
    end_epoch_s = Column(Float, nullable=False)
    duration_seconds = Column(Float, nullable=False)
    p_idle_threshold_kw = Column(Float, nullable=False)
    t_delay_seconds = Column(Float, nullable=False)
    total_idle_energy_kwh = Column(Float, nullable=False)
    avoidable_energy_kwh = Column(Float, default=0.0) # > 0 only if eligible
    eligible = Column(Boolean, default=False)
    provenance = Column(SQLEnum(ProvenanceType), default=ProvenanceType.DERIVED)
    model_version = Column(String(20), default="1.0.0-prototype")
    created_at = Column(DateTime, default=utcnow)
    
    equipment = relationship("Equipment", back_populates="idle_periods")

class Decision(Base):
    __tablename__ = "decisions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    equipment_id = Column(String(50), ForeignKey("equipment.id"), nullable=False, index=True)
    scenario_id = Column(String(50), index=True)
    timestamp = Column(DateTime, default=utcnow, index=True)
    evaluation_step = Column(Integer, nullable=False) # 1 to 8
    outcome = Column(SQLEnum(DecisionOutcome), nullable=False)
    reason = Column(String(255), nullable=False)
    decision_trace = Column(JSON, nullable=False) # Detailed 8-step trace
    recommendation_text = Column(Text)
    approval_required = Column(Boolean, default=False)
    approval_id = Column(Integer, ForeignKey("approvals.id"), nullable=True)
    provenance = Column(SQLEnum(ProvenanceType), default=ProvenanceType.DERIVED)
    created_at = Column(DateTime, default=utcnow)
    
    equipment = relationship("Equipment", back_populates="decisions")
    approval = relationship("Approval", foreign_keys=[approval_id])

class Approval(Base):
    __tablename__ = "approvals"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    equipment_id = Column(String(50), nullable=False, index=True)
    scenario_id = Column(String(50))
    action_type = Column(String(50), default="SIMULATED_SHUTDOWN")
    status = Column(String(20), default="PENDING") # PENDING, APPROVED, REJECTED, EXPIRED
    requested_at = Column(DateTime, default=utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(String(100), nullable=True)
    user_role = Column(SQLEnum(UserRole), nullable=True)
    comment = Column(String(255), nullable=True)
    estimated_kwh_saving = Column(Float, default=0.0)
    provenance = Column(SQLEnum(ProvenanceType), default=ProvenanceType.DERIVED)

class ControlCommand(Base):
    __tablename__ = "control_commands"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    equipment_id = Column(String(50), ForeignKey("equipment.id"), nullable=False, index=True)
    approval_id = Column(Integer, ForeignKey("approvals.id"), nullable=True)
    command_type = Column(String(50), nullable=False) # SIMULATED_SHUTDOWN, SIMULATED_RESTART, MANUAL_OVERRIDE
    target_interface = Column(String(50), default="SIMULATED_CONTACTOR_VFD")
    simulated_command_label = Column(String(50), default="SIMULATED COMMAND")
    status = Column(String(20), default="EXECUTED") # EXECUTED, BLOCKED, FAILED
    issued_by = Column(String(100), nullable=False)
    issued_at = Column(DateTime, default=utcnow)
    completed_at = Column(DateTime, default=utcnow)
    details = Column(JSON, nullable=True)
    provenance = Column(SQLEnum(ProvenanceType), default=ProvenanceType.SIMULATED)
    
    equipment = relationship("Equipment", back_populates="control_commands")

class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_uid = Column(String(50), unique=True, index=True)
    equipment_id = Column(String(50), nullable=False, index=True)
    scenario_id = Column(String(50), index=True)
    severity = Column(SQLEnum(EventSeverity), default=EventSeverity.MONITOR)
    event_code = Column(String(50), nullable=False)
    parameter = Column(String(50), nullable=False) # Voltage, Frequency, PowerFactor, IdleDuration, Interlock, etc.
    observed_value = Column(Float, nullable=True)
    threshold_reference = Column(Float, nullable=True)
    deviation = Column(Float, nullable=True)
    unit = Column(String(20), default="")
    engineering_explanation = Column(Text, nullable=False)
    recommended_consideration = Column(Text, nullable=False) # Non-binding advisory
    status = Column(String(20), default="ACTIVE") # ACTIVE, ACKNOWLEDGED, RESOLVED
    occurrence_count = Column(Integer, default=1)
    started_at = Column(DateTime, default=utcnow)
    last_detected_at = Column(DateTime, default=utcnow)
    resolved_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String(100), nullable=True)
    provenance = Column(SQLEnum(ProvenanceType), default=ProvenanceType.DERIVED)

class Scenario(Base):
    __tablename__ = "scenarios"
    
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    seed = Column(Integer, default=42)
    duration_hours = Column(Float, default=8.0)
    is_active = Column(Boolean, default=False)
    generated_at = Column(DateTime, default=utcnow)
    provenance = Column(SQLEnum(ProvenanceType), default=ProvenanceType.SIMULATED)

class BaselineRun(Base):
    __tablename__ = "baseline_runs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    scenario_id = Column(String(50), nullable=False, index=True)
    run_type = Column(String(20), nullable=False) # BASELINE, OPTIMISED
    seed = Column(Integer, nullable=False)
    total_energy_kwh = Column(Float, nullable=False)
    idle_energy_kwh = Column(Float, nullable=False)
    avoidable_energy_kwh = Column(Float, nullable=False)
    estimated_savings_kwh = Column(Float, default=0.0)
    estimated_cost_savings = Column(Float, default=0.0)
    estimated_emissions_kg_co2 = Column(Float, default=0.0)
    idle_share_percent = Column(Float, default=0.0)
    provenance = Column(SQLEnum(ProvenanceType), default=ProvenanceType.DERIVED)
    created_at = Column(DateTime, default=utcnow)

class DataQualityCheck(Base):
    __tablename__ = "data_quality_checks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    telemetry_id = Column(Integer, nullable=True)
    equipment_id = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=utcnow)
    check_type = Column(String(50), nullable=False) # OUT_OF_RANGE_VOLTAGE, OUT_OF_RANGE_FREQ, MISSING_DATA, SENSOR_FAULT
    raw_payload = Column(JSON, nullable=False)
    status = Column(String(20), default="REJECTED")
    action_taken = Column(String(255), default="Excluded from energy & idle analysis; flagged for maintenance check.")
    provenance = Column(SQLEnum(ProvenanceType), default=ProvenanceType.DERIVED)

class ImportRun(Base):
    __tablename__ = "import_runs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False) # CSV, JSON
    record_count = Column(Integer, default=0)
    valid_count = Column(Integer, default=0)
    warning_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    summary = Column(JSON, nullable=False)
    schema_version = Column(String(20), default="1.0.0")
    provenance = Column(SQLEnum(ProvenanceType), default=ProvenanceType.IMPORTED)
    imported_at = Column(DateTime, default=utcnow)

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(String(50), primary_key=True)
    title = Column(String(255), nullable=False)
    report_type = Column(String(50), default="ENERGY_ASSESSMENT")
    scenario_id = Column(String(50))
    generated_at = Column(DateTime, default=utcnow)
    data = Column(JSON, nullable=False)
    provenance = Column(SQLEnum(ProvenanceType), default=ProvenanceType.DERIVED)
    model_version = Column(String(20), default="1.0.0-prototype")

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(50), primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.OPERATOR)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)

class AuditLog(Base):
    __tablename__ = "audit_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=utcnow)
    user_id = Column(String(50), nullable=False)
    role = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False) # APPROVE_SHUTDOWN, REJECT_SHUTDOWN, MANUAL_OVERRIDE, RESTART, UPDATE_SETTINGS
    entity = Column(String(50), nullable=False)
    entity_id = Column(String(50), nullable=True)
    details = Column(JSON, nullable=True)
    provenance = Column(SQLEnum(ProvenanceType), default=ProvenanceType.DERIVED)
