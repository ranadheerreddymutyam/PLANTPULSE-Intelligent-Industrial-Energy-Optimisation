"""Alert and Event Engine with Flood Prevention (Debounce & Hysteresis).

Rule-based, deterministic monitoring layer. Groups events so continuous anomalies
do not flood operator logs or alert queues.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from app.core.provenance import EventSeverity, ProvenanceType
from app.models.entities import Event, SiteConfig, Equipment

def utcnow():
    return datetime.now(timezone.utc)

class AlertEngine:
    def __init__(self, debounce_count: int = 3, hysteresis_seconds: int = 300):
        self.debounce_count = debounce_count
        self.hysteresis_seconds = hysteresis_seconds
        # In-memory tracking of consecutive sample counts: {f"{equipment_id}:{event_code}": count}
        self.sample_counters: Dict[str, int] = {}
        # Tracking last active timestamp: {f"{equipment_id}:{event_code}": datetime}
        self.last_seen: Dict[str, datetime] = {}
        
    def evaluate_telemetry_sample(
        self,
        db_session: Any,
        equipment: Equipment,
        site_config: SiteConfig,
        telemetry: Dict[str, Any],
        scenario_id: Optional[str] = None
    ) -> List[Event]:
        """Evaluates a single telemetry record and manages grouped events in the database."""
        generated_events: List[Event] = []
        now = utcnow()
        
        voltage_v = telemetry.get("voltage_v")
        current_a = telemetry.get("current_a")
        freq_hz = telemetry.get("frequency_hz", 50.0)
        pf = telemetry.get("power_factor", 0.85)
        kw = telemetry.get("active_power_kw", 0.0)
        
        v_min = site_config.voltage_min_v
        v_max = site_config.voltage_max_v
        f_min = site_config.frequency_min_hz
        f_max = site_config.frequency_max_hz
        pf_min = site_config.power_factor_min
        rated_i = equipment.rated_current_a
        
        checks = []
        
        # 1. Voltage out of range
        if voltage_v is not None and (voltage_v < v_min or voltage_v > v_max):
            dev = round(voltage_v - (v_min if voltage_v < v_min else v_max), 2)
            checks.append({
                "code": "VOLT_OUT_OF_SPEC",
                "parameter": "Voltage",
                "severity": EventSeverity.ATTENTION,
                "observed": voltage_v,
                "threshold": v_min if voltage_v < v_min else v_max,
                "deviation": dev,
                "unit": "V",
                "explanation": f"Line voltage {voltage_v} V outside allowable 3-phase range [{v_min}, {v_max}] V.",
                "recommendation": "Inspect transformer tap changer, utility supply balance, or feeder cables."
            })
            
        # 2. Frequency out of range
        if freq_hz is not None and (freq_hz < f_min or freq_hz > f_max):
            dev = round(freq_hz - (f_min if freq_hz < f_min else f_max), 2)
            checks.append({
                "code": "FREQ_OUT_OF_SPEC",
                "parameter": "Frequency",
                "severity": EventSeverity.WARNING,
                "observed": freq_hz,
                "threshold": f_min if freq_hz < f_min else f_max,
                "deviation": dev,
                "unit": "Hz",
                "explanation": f"Supply frequency {freq_hz} Hz deviates from grid nominal [{f_min}, {f_max}] Hz.",
                "recommendation": "Verify plant generator governing or check for grid frequency instability."
            })
            
        # 3. Overcurrent
        if current_a is not None and current_a > rated_i:
            dev = round(current_a - rated_i, 2)
            checks.append({
                "code": "OVERCURRENT",
                "parameter": "Current",
                "severity": EventSeverity.WARNING,
                "observed": current_a,
                "threshold": rated_i,
                "deviation": dev,
                "unit": "A",
                "explanation": f"Operating current {current_a} A exceeds equipment rated thermal full-load current {rated_i} A.",
                "recommendation": "Inspect mechanical loading, bearings, pump impellers, and starter contacts."
            })
            
        # 4. Low Power Factor
        if pf is not None and kw > 2.0 and pf < pf_min:
            dev = round(pf - pf_min, 3)
            checks.append({
                "code": "LOW_POWER_FACTOR",
                "parameter": "Power Factor",
                "severity": EventSeverity.MONITOR,
                "observed": pf,
                "threshold": pf_min,
                "deviation": dev,
                "unit": "dimensionless",
                "explanation": f"Displacement power factor {pf} below reference minimum {pf_min} during operation.",
                "recommendation": "Check power factor correction capacitor banks or harmonic filter health."
            })
            
        # 5. Interlock Engaged
        estop = telemetry.get("interlock_estop", False)
        overload = telemetry.get("interlock_overload", False)
        if estop or overload:
            cause = "Emergency Stop" if estop else "Thermal Overload"
            checks.append({
                "code": "INTERLOCK_ENGAGED",
                "parameter": "Safety Interlock",
                "severity": EventSeverity.ATTENTION,
                "observed": 1.0,
                "threshold": 0.0,
                "deviation": 1.0,
                "unit": "binary",
                "explanation": f"Safety interlock circuit tripped ({cause}). Automated commands blocked.",
                "recommendation": "Address physical field condition before clearing safety circuit."
            })
            
        # Process checks with debounce & hysteresis
        active_codes = set()
        for check in checks:
            key = f"{equipment.id}:{check['code']}"
            active_codes.add(key)
            self.sample_counters[key] = self.sample_counters.get(key, 0) + 1
            self.last_seen[key] = now
            
            # Check debounce threshold (e.g. 3 consecutive samples)
            if self.sample_counters[key] >= site_config.alert_debounce_count:
                # Find or update active grouped event
                existing_event = (
                    db_session.query(Event)
                    .filter(
                        Event.equipment_id == equipment.id,
                        Event.event_code == check["code"],
                        Event.status.in_(["ACTIVE", "ACKNOWLEDGED"])
                    )
                    .first()
                )
                
                if existing_event:
                    # Update occurrence count and last detected
                    existing_event.occurrence_count += 1
                    existing_event.last_detected_at = now
                    existing_event.observed_value = check["observed"]
                    existing_event.deviation = check["deviation"]
                    db_session.add(existing_event)
                    generated_events.append(existing_event)
                else:
                    # Create new grouped event
                    uid = f"EVT-{equipment.id[:8]}-{check['code'][:8]}-{int(now.timestamp())}"
                    new_evt = Event(
                        event_uid=uid,
                        equipment_id=equipment.id,
                        scenario_id=scenario_id,
                        severity=check["severity"],
                        event_code=check["code"],
                        parameter=check["parameter"],
                        observed_value=check["observed"],
                        threshold_reference=check["threshold"],
                        deviation=check["deviation"],
                        unit=check["unit"],
                        engineering_explanation=check["explanation"],
                        recommended_consideration=check["recommendation"],
                        status="ACTIVE",
                        occurrence_count=1,
                        started_at=now,
                        last_detected_at=now,
                        provenance=ProvenanceType.DERIVED
                    )
                    db_session.add(new_evt)
                    generated_events.append(new_evt)
                    
        # Check hysteresis for existing events that haven't been seen recently
        active_events = (
            db_session.query(Event)
            .filter(
                Event.equipment_id == equipment.id,
                Event.status == "ACTIVE"
            )
            .all()
        )
        
        for evt in active_events:
            key = f"{equipment.id}:{evt.event_code}"
            if key not in active_codes:
                last_time = self.last_seen.get(key, evt.last_detected_at)
                # If hysteresis duration has elapsed without new samples, resolve
                if last_time and (now - last_time).total_seconds() >= site_config.alert_hysteresis_seconds:
                    evt.status = "RESOLVED"
                    evt.resolved_at = now
                    self.sample_counters[key] = 0
                    db_session.add(evt)
                    
        db_session.commit()
        return generated_events

alert_engine = AlertEngine()
