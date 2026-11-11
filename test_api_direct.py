"""Direct unit tests for API route functions without socket/network overhead."""
import pytest
from app.core.database import SessionLocal
from app.api.routers import (
    analytics, equipment, idle, decisions, control, savings, events, reports, scenarios, auth, config
)
from app.schemas.domain import (
    EquipmentUpdate, ApprovalActionRequest, SimulatedCommandRequest, ScenarioSwitchRequest,
    EventActionRequest, UserLoginRequest
)
from app.core.provenance import UserRole

@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    yield session
    session.close()

def test_analytics_dashboard(db):
    data = analytics.get_dashboard_overview(db=db)
    assert "headline_sentence" in data
    assert data["total_equipment_count"] == 8
    assert "PROPOSED CONCEPT" in data["project_status"]
    assert "SIMULATED / DEMONSTRATION DATA" in data["data_provenance"]
    assert "sparkline" in data
    assert len(data["sparkline"]) > 0

def test_equipment_listing_and_critical_exclusion(db):
    eq_list = equipment.list_equipment(db=db)
    assert len(eq_list) == 8
    
    # Verify critical load permanent exclusion rule
    main_motor = next(e for e in eq_list if e.id == "eq_main_process_motor")
    assert main_motor.criticality.value == "CRITICAL"
    assert main_motor.eligible_for_shutdown is False
    
    # Attempt to enable shutdown on critical motor -> MUST REMAIN FALSE
    updated = equipment.update_equipment(
        equipment_id="eq_main_process_motor",
        payload=EquipmentUpdate(eligible_for_shutdown=True),
        db=db
    )
    assert updated.eligible_for_shutdown is False

def test_idle_ranking(db):
    ranking_data = idle.get_loss_ranking(db=db)
    assert "Where does the loss occur?" in ranking_data["title"]
    assert len(ranking_data["ranking"]) == 8
    # Top rank should have highest avoidable energy
    assert ranking_data["ranking"][0]["avoidable_idle_energy_kwh"] >= ranking_data["ranking"][-1]["avoidable_idle_energy_kwh"]

def test_decisions_and_tradeoffs(db):
    decisions_list = decisions.get_latest_decisions_all(db=db)
    assert len(decisions_list) == 8
    # Check decision trace format
    for d in decisions_list:
        assert len(d.decision_trace) >= 2
        
    tradeoffs_data = decisions.get_tradeoff_checklist()
    assert len(tradeoffs_data["tradeoffs"]) >= 4
    categories = [t["category"] for t in tradeoffs_data["tradeoffs"]]
    assert "Electrical & Thermal Stress" in categories
    assert "Safety & Critical Service" in categories

def test_control_approval_and_critical_rejection(db):
    approvals = control.list_approvals(db=db)
    assert isinstance(approvals, list)
    
    # Test rejection of controlled shutdown on critical load
    with pytest.raises(Exception) as excinfo:
        control.issue_simulated_command(
            payload=SimulatedCommandRequest(
                equipment_id="eq_main_process_motor",
                command_type="SIMULATED_SHUTDOWN",
                user_id="operator",
                user_role=UserRole.OPERATOR
            ),
            db=db
        )
    assert "CRITICAL LOAD HARD LOCK" in str(excinfo.value.detail)

def test_control_simulated_restart_on_eligible(db):
    cmd = control.issue_simulated_command(
        payload=SimulatedCommandRequest(
            equipment_id="eq_conveyor_motor",
            command_type="SIMULATED_RESTART",
            user_id="operator",
            user_role=UserRole.OPERATOR,
            reason="Test restart verification"
        ),
        db=db
    )
    assert cmd.simulated_command_label == "SIMULATED COMMAND"
    assert cmd.status == "EXECUTED"

def test_interlocks_panel(db):
    interlocks_data = control.get_interlocks_status(db=db)
    assert len(interlocks_data["interlocks"]) == 8
    crit = next(i for i in interlocks_data["interlocks"] if i["equipment_id"] == "eq_main_process_motor")
    assert crit["can_shutdown"] is False # Critical equipment can never be shut down

def test_savings_baseline_comparison(db):
    comp = savings.get_baseline_comparison(db=db)
    assert comp["comparison_available"] is True
    assert "fairness_guarantee" in comp["assumptions"]

def test_live_reports_assessment(db):
    rep = reports.get_live_assessment(db=db)
    assert rep["header_banner"] == "PROTOTYPE ENGINEERING ASSESSMENT — SIMULATED DATA"
    assert "pilot_plan" in rep
    assert len(rep["pilot_plan"]["roadmap_stages"]) == 6
    assert rep["pilot_plan"]["roadmap_stages"][0]["status"] == "IN PROGRESS"
    assert rep["pilot_plan"]["roadmap_stages"][1]["status"] == "PLANNED / NOT IMPLEMENTED"
    assert "Water use / material loss / waste generated: Not in scope of current prototype (energy only)." in rep["measures"]["out_of_scope_notice"]

def test_scenarios_listing(db):
    scens = scenarios.list_scenarios(db=db)
    assert len(scens) == 7
    ids = [s.id for s in scens]
    assert "scenario_normal_shift" in ids
    assert "scenario_heavy_idle" in ids
    assert "scenario_intermittent_short" in ids
    assert "scenario_critical_load_idle" in ids
    assert "scenario_interlock_blocked" in ids
    assert "scenario_sensor_fault" in ids
    assert "scenario_optimised_run" in ids

def test_auth_login(db):
    res = auth.login(UserLoginRequest(username="operator", password="operator123"), db=db)
    assert res.user.role == UserRole.OPERATOR
    assert "operator" in res.access_token
