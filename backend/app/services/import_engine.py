"""Data Import Pipeline for CSV and JSON telemetry.

Validates schemas, timestamps, ranges, checks duplicates, computes derived active power if omitted,
and assigns provenance=IMPORTED.
"""
import csv
import json
import io
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from app.core.provenance import ProvenanceType, OperatingState
from app.models.entities import Telemetry, Equipment, ImportRun, SiteConfig
from app.engineering.calculations import compute_apparent_power, compute_active_power, compute_power_factor, compute_reactive_power

REQUIRED_FIELDS = ["timestamp", "equipment_id", "voltage", "current"]
OPTIONAL_FIELDS = ["kw", "kwh", "power_factor", "frequency", "operating_status"]

def generate_sample_csv() -> str:
    """Generates a downloadable sample CSV with valid structure for reference."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "timestamp", "equipment_id", "voltage", "current", "kw", "power_factor", "frequency", "operating_status"
    ])
    now = datetime.now(timezone.utc)
    for i in range(10):
        t_iso = (now.replace(microsecond=0)).isoformat()
        writer.writerow([
            t_iso,
            "eq_conveyor_motor",
            415.2,
            12.5,
            4.8,
            0.53,
            50.0,
            "RUNNING"
        ])
    return output.getvalue()

def preview_import_data(file_content: str, file_type: str = "CSV") -> Dict[str, Any]:
    """Generates a structured preview of the file before ingestion."""
    rows = []
    headers = []
    
    if file_type.upper() == "CSV":
        reader = csv.reader(io.StringIO(file_content))
        try:
            headers = [h.strip().lower() for h in next(reader, [])]
        except Exception as e:
            return {"error": f"Failed to parse CSV headers: {str(e)}"}
            
        for idx, r in enumerate(reader):
            if idx >= 10:
                break
            if r:
                rows.append(r)
    else: # JSON
        try:
            data = json.loads(file_content)
            if isinstance(data, list) and len(data) > 0:
                headers = list(data[0].keys())
                rows = [list(item.values()) for item in data[:10]]
            else:
                return {"error": "JSON file must contain an array of telemetry objects."}
        except Exception as e:
            return {"error": f"Failed to parse JSON file: {str(e)}"}
            
    # Check header coverage
    missing_required = [f for f in REQUIRED_FIELDS if f not in headers]
    
    return {
        "headers": headers,
        "preview_rows": rows,
        "sample_count": len(rows),
        "missing_required_fields": missing_required,
        "is_valid_schema": len(missing_required) == 0
    }

def process_telemetry_import(
    db_session: Any,
    filename: str,
    file_content: str,
    file_type: str = "CSV",
    field_mapping: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Parses, validates, and imports records into the telemetry table."""
    records_to_process = []
    
    if file_type.upper() == "CSV":
        reader = csv.DictReader(io.StringIO(file_content))
        raw_headers = [h.strip() for h in (reader.fieldnames or [])]
        # Clean headers
        mapping = field_mapping or {h.strip().lower(): h.strip().lower() for h in raw_headers}
        for r in reader:
            normalized_row = {}
            for k, v in r.items():
                if k is not None:
                    target_key = mapping.get(k.strip().lower(), k.strip().lower())
                    normalized_row[target_key] = v.strip() if v else None
            records_to_process.append(normalized_row)
    else:
        try:
            data = json.loads(file_content)
            if not isinstance(data, list):
                raise ValueError("JSON content must be a list of telemetry objects.")
            records_to_process = data
        except Exception as e:
            raise ValueError(f"Malformed JSON: {str(e)}")
            
    valid_records = []
    warnings = []
    errors = []
    seen_keys = set()
    
    # Pre-fetch existing equipment IDs
    known_equipment_ids = {eq.id for eq in db_session.query(Equipment.id).all()}
    site = db_session.query(SiteConfig).first()
    v_nominal = site.nominal_voltage_v if site else 415.0
    
    for idx, row in enumerate(records_to_process):
        row_num = idx + 1
        
        # Check required fields
        eq_id = row.get("equipment_id")
        t_str = row.get("timestamp")
        v_str = row.get("voltage")
        i_str = row.get("current")
        
        if not eq_id or not t_str or v_str is None or i_str is None:
            errors.append(f"Row {row_num}: Missing required field (timestamp, equipment_id, voltage, current).")
            continue
            
        if eq_id not in known_equipment_ids:
            errors.append(f"Row {row_num}: Unknown equipment_id '{eq_id}'. Configure equipment before import.")
            continue
            
        # Parse timestamp
        try:
            if "T" in t_str or "-" in t_str:
                dt = datetime.fromisoformat(t_str.replace("Z", "+00:00"))
            else:
                dt = datetime.fromtimestamp(float(t_str), tz=timezone.utc)
            epoch_s = dt.timestamp()
        except Exception as e:
            errors.append(f"Row {row_num}: Invalid timestamp format '{t_str}': {str(e)}")
            continue
            
        # Duplicate detection (equipment_id + timestamp)
        dup_key = f"{eq_id}:{int(epoch_s)}"
        if dup_key in seen_keys:
            warnings.append(f"Row {row_num}: Duplicate timestamp for {eq_id} at {t_str}. Skipped.")
            continue
        seen_keys.add(dup_key)
        
        # Parse numericals
        try:
            v_val = float(v_str)
            i_val = float(i_str)
        except ValueError:
            errors.append(f"Row {row_num}: Voltage '{v_str}' or Current '{i_str}' is not a valid number.")
            continue
            
        # Physical plausibility range checks
        if v_val < 200 or v_val > 600:
            warnings.append(f"Row {row_num}: Voltage {v_val} V is outside plausible industrial range [200, 600] V.")
        if i_val < 0 or i_val > 1000:
            warnings.append(f"Row {row_num}: Current {i_val} A is outside plausible range [0, 1000] A.")
            
        # Optional fields
        kw_val = float(row["kw"]) if row.get("kw") not in (None, "") else None
        pf_val = float(row["power_factor"]) if row.get("power_factor") not in (None, "") else 0.85
        freq_val = float(row["frequency"]) if row.get("frequency") not in (None, "") else 50.0
        kwh_val = float(row["kwh"]) if row.get("kwh") not in (None, "") else 0.0
        raw_st = str(row.get("operating_status") or "RUNNING").upper()
        
        op_st = OperatingState.RUNNING
        if raw_st in ("STOP", "STOPPED", "OFF"):
            op_st = OperatingState.STOPPED
        elif raw_st in ("IDLE", "STANDBY"):
            op_st = OperatingState.IDLE
            
        # Centralized engineering calculations
        s_eng = compute_apparent_power(v_val, i_val, provenance=ProvenanceType.IMPORTED)
        p_eng = compute_active_power(v_val, i_val, pf_val, metered_kw=kw_val, provenance=ProvenanceType.IMPORTED)
        pf_eng = compute_power_factor(p_eng.value, s_eng.value, provenance=ProvenanceType.IMPORTED)
        q_eng = compute_reactive_power(s_eng.value, p_eng.value, provenance=ProvenanceType.IMPORTED)
        
        tel = Telemetry(
            equipment_id=eq_id,
            scenario_id="imported_dataset",
            timestamp=dt,
            timestamp_epoch_s=epoch_s,
            voltage_v=round(v_val, 2),
            current_a=round(i_val, 2),
            power_factor=pf_eng.value or 0.85,
            frequency_hz=round(freq_val, 2),
            active_power_kw=p_eng.value or 0.0,
            apparent_power_kva=s_eng.value or 0.0,
            reactive_power_kvar=q_eng.value or 0.0,
            cumulative_energy_kwh=round(kwh_val, 4),
            operating_state=op_st,
            interlock_estop=False,
            interlock_overload=False,
            interlock_process_permissive=True,
            interlock_manual_override=False,
            provenance=ProvenanceType.IMPORTED,
            model_version="1.0.0-prototype"
        )
        valid_records.append(tel)
        
    if valid_records:
        db_session.bulk_save_objects(valid_records)
        
    summary_data = {
        "filename": filename,
        "total_records_in_file": len(records_to_process),
        "valid_imported_records": len(valid_records),
        "warning_count": len(warnings),
        "error_count": len(errors),
        "warnings_sample": warnings[:10],
        "errors_sample": errors[:10]
    }
    
    import_run = ImportRun(
        filename=filename,
        file_type=file_type.upper(),
        record_count=len(records_to_process),
        valid_count=len(valid_records),
        warning_count=len(warnings),
        error_count=len(errors),
        summary=summary_data,
        schema_version="1.0.0",
        provenance=ProvenanceType.IMPORTED
    )
    db_session.add(import_run)
    db_session.commit()
    
    return summary_data
