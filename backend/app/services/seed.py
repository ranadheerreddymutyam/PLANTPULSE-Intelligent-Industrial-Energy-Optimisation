"""Database initialization and initial seeding script."""
import hashlib
from app.core.database import engine, SessionLocal, Base
from app.core.provenance import UserRole, EquipmentCriticality, ProvenanceType
from app.models.entities import SiteConfig, Equipment, Scenario, User
from app.services.scenario_engine import SCENARIO_DEFINITIONS, generate_scenario_telemetry

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def seed_database():
    """Initializes tables and seeds default demonstration configuration and telemetry."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # 1. Site Config
        site = db.query(SiteConfig).filter_by(id="site_demo_01").first()
        if not site:
            site = SiteConfig(
                id="site_demo_01",
                site_name="Industrial Manufacturing Feeder A",
                description="3-Phase 415 V line-to-line distribution feeder powering production and auxiliary units.",
                nominal_voltage_v=415.0,
                nominal_frequency_hz=50.0,
                voltage_min_v=373.5,
                voltage_max_v=456.5,
                frequency_min_hz=47.5,
                frequency_max_hz=52.5,
                power_factor_min=0.80,
                tariff_per_kwh=0.18,
                currency="USD",
                emission_factor_kg_co2_per_kwh=0.42,
                restart_allowance_kwh=0.0,
                alert_debounce_count=3,
                alert_hysteresis_seconds=300,
                config_version="1.0.0",
                provenance=ProvenanceType.CONFIGURED
            )
            db.add(site)
            db.commit()
            print("SiteConfig seeded.")
            
        # 2. Equipment Entities
        equipment_data = [
            {
                "id": "eq_main_process_motor",
                "name": "Main Process Extruder Motor",
                "type": "motor",
                "rated_kw": 75.0,
                "rated_a": 130.0,
                "p_idle_kw": 15.0,
                "t_delay": 180.0,
                "criticality": EquipmentCriticality.CRITICAL,
                "eligible": False, # Permanently false
                "vfd": True,
                "min_off": 300,
                "restart_delay": 120,
                "max_restarts": 3
            },
            {
                "id": "eq_cooling_water_pump",
                "name": "Cooling Tower Circulation Pump",
                "type": "pump",
                "rated_kw": 45.0,
                "rated_a": 78.0,
                "p_idle_kw": 10.0,
                "t_delay": 180.0,
                "criticality": EquipmentCriticality.CRITICAL,
                "eligible": False, # Permanently false
                "vfd": False,
                "min_off": 300,
                "restart_delay": 120,
                "max_restarts": 3
            },
            {
                "id": "eq_conveyor_motor",
                "name": "Assembly Infeed Conveyor Motor",
                "type": "motor",
                "rated_kw": 22.0,
                "rated_a": 39.0,
                "p_idle_kw": 5.0,
                "t_delay": 120.0,
                "criticality": EquipmentCriticality.NON_CRITICAL,
                "eligible": True,
                "vfd": True,
                "min_off": 180,
                "restart_delay": 60,
                "max_restarts": 6
            },
            {
                "id": "eq_exhaust_fan",
                "name": "Fume Extraction Exhaust Fan",
                "type": "fan",
                "rated_kw": 30.0,
                "rated_a": 52.0,
                "p_idle_kw": 7.0,
                "t_delay": 120.0,
                "criticality": EquipmentCriticality.NON_CRITICAL,
                "eligible": True,
                "vfd": True,
                "min_off": 180,
                "restart_delay": 60,
                "max_restarts": 4
            },
            {
                "id": "eq_air_compressor",
                "name": "Pneumatic Utility Air Compressor",
                "type": "auxiliary",
                "rated_kw": 55.0,
                "rated_a": 95.0,
                "p_idle_kw": 14.0,
                "t_delay": 240.0,
                "criticality": EquipmentCriticality.NON_CRITICAL,
                "eligible": True,
                "vfd": False,
                "min_off": 360,
                "restart_delay": 180,
                "max_restarts": 4
            },
            {
                "id": "eq_mixer_drive",
                "name": "Slurry Vessel Mixer Drive",
                "type": "motor",
                "rated_kw": 37.0,
                "rated_a": 64.0,
                "p_idle_kw": 8.0,
                "t_delay": 180.0,
                "criticality": EquipmentCriticality.NON_CRITICAL,
                "eligible": True,
                "vfd": True,
                "min_off": 240,
                "restart_delay": 90,
                "max_restarts": 4
            },
            {
                "id": "eq_auxiliary_pump",
                "name": "Washdown Auxiliary Water Pump",
                "type": "pump",
                "rated_kw": 15.0,
                "rated_a": 26.0,
                "p_idle_kw": 3.5,
                "t_delay": 90.0,
                "criticality": EquipmentCriticality.NON_CRITICAL,
                "eligible": True,
                "vfd": False,
                "min_off": 120,
                "restart_delay": 60,
                "max_restarts": 6
            },
            {
                "id": "eq_packing_feeder",
                "name": "End-of-Line Packaging Feeder",
                "type": "auxiliary",
                "rated_kw": 18.5,
                "rated_a": 32.0,
                "p_idle_kw": 4.0,
                "t_delay": 120.0,
                "criticality": EquipmentCriticality.NON_CRITICAL,
                "eligible": True,
                "vfd": True,
                "min_off": 180,
                "restart_delay": 60,
                "max_restarts": 6
            }
        ]
        
        for eq_spec in equipment_data:
            existing = db.query(Equipment).filter_by(id=eq_spec["id"]).first()
            if not existing:
                # Critical load permanent exclusion rule
                is_crit = (eq_spec["criticality"] == EquipmentCriticality.CRITICAL)
                el_flag = False if is_crit else eq_spec["eligible"]
                
                eq = Equipment(
                    id=eq_spec["id"],
                    site_id="site_demo_01",
                    name=eq_spec["name"],
                    equipment_type=eq_spec["type"],
                    rated_power_kw=eq_spec["rated_kw"],
                    rated_current_a=eq_spec["rated_a"],
                    p_idle_threshold_kw=eq_spec["p_idle_kw"],
                    t_delay_seconds=eq_spec["t_delay"],
                    criticality=eq_spec["criticality"],
                    eligible_for_shutdown=el_flag,
                    vfd_capable=eq_spec["vfd"],
                    min_off_time_seconds=eq_spec["min_off"],
                    restart_delay_seconds=eq_spec["restart_delay"],
                    max_restarts_per_hour=eq_spec["max_restarts"],
                    provenance=ProvenanceType.CONFIGURED,
                    config_version="1.0.0"
                )
                db.add(eq)
        db.commit()
        print("Equipment entities seeded.")
        
        # 3. Scenarios
        for s_def in SCENARIO_DEFINITIONS:
            sc = db.query(Scenario).filter_by(id=s_def["id"]).first()
            if not sc:
                sc = Scenario(
                    id=s_def["id"],
                    name=s_def["name"],
                    description=s_def["description"],
                    seed=s_def["seed"],
                    duration_hours=s_def["duration_hours"],
                    is_active=(s_def["id"] == "scenario_heavy_idle"),
                    provenance=ProvenanceType.SIMULATED
                )
                db.add(sc)
        db.commit()
        print("Scenarios seeded.")
        
        # 4. Users (Role-based access)
        demo_users = [
            ("usr_operator", "operator", "John Doe (Shift Operator)", UserRole.OPERATOR, "operator123"),
            ("usr_energy_mgr", "energymgr", "Sarah Jenkins (Plant Energy Manager)", UserRole.ENERGY_MANAGER, "energy123"),
            ("usr_maintenance", "maintenance", "Carlos Gomez (Electrical Maintenance)", UserRole.MAINTENANCE, "maint123"),
            ("usr_admin", "admin", "Admin System Controller", UserRole.ADMIN, "admin123")
        ]
        for u_id, uname, fname, role, pw in demo_users:
            u = db.query(User).filter_by(username=uname).first()
            if not u:
                u = User(
                    id=u_id,
                    username=uname,
                    full_name=fname,
                    role=role,
                    hashed_password=hash_pw(pw),
                    is_active=True
                )
                db.add(u)
        db.commit()
        print("Default users seeded.")
        
        # 5. Populate initial telemetry with scenario_heavy_idle
        print("Generating initial physical telemetry for Heavy Idle scenario...")
        generate_scenario_telemetry(db, "scenario_heavy_idle")
        print("Initial telemetry generated successfully.")
        
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
