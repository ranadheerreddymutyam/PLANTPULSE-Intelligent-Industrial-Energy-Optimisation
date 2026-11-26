"""Data Provenance & Value Metadata definitions."""
from enum import Enum
from typing import Any, Dict, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class ProvenanceType(str, Enum):
    SIMULATED = "SIMULATED"
    IMPORTED = "IMPORTED"
    DERIVED = "DERIVED"
    ESTIMATED = "ESTIMATED"
    CONFIGURED = "CONFIGURED"

class UserRole(str, Enum):
    OPERATOR = "OPERATOR"
    ENERGY_MANAGER = "ENERGY_MANAGER"
    MAINTENANCE = "MAINTENANCE"
    ADMIN = "ADMIN"

class EquipmentCriticality(str, Enum):
    CRITICAL = "CRITICAL"
    NON_CRITICAL = "NON_CRITICAL"

class OperatingState(str, Enum):
    RUNNING = "RUNNING"
    IDLE = "IDLE"
    STOPPED = "STOPPED"
    FAULT = "FAULT"

class DecisionOutcome(str, Enum):
    ACTIVELY_REQUIRED = "ACTIVELY REQUIRED"
    SUSTAINED_IDLE = "SUSTAINED IDLE"
    APPROVED_NON_CRITICAL = "APPROVED NON-CRITICAL"
    REJECTED_INPUT_FAULT = "REJECTED (INPUT FAULT)"
    BLOCKED_CRITICAL = "BLOCKED (CRITICAL LOAD)"
    BLOCKED_INTERLOCK = "BLOCKED (INTERLOCK ACTIVE)"
    BLOCKED_RESTART_PROTECTION = "BLOCKED (RESTART PROTECTION)"

class EventSeverity(str, Enum):
    NORMAL = "NORMAL"
    MONITOR = "MONITOR"
    WARNING = "WARNING"
    ATTENTION = "ATTENTION"

class EngineeringValue(BaseModel):
    value: Optional[float] = None
    unit: str
    formula: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    provenance: ProvenanceType
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    model_version: str = "1.0.0-prototype"
    label: Optional[str] = None
    note: Optional[str] = None
