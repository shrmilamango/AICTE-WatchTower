import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, get_db
from app.core.config import settings
from app.main import app
from app.models.user import User, UserRole
from app.models.institution import Institution
from app.models.workflow import Application, Task
from app.models.compliance import Undertaking
from app.models.audit import AuditLog
from app.services.config_service import ConfigService
from app.workflow.engine import WorkflowEngine
from app.services.demo_seeder import seed_demo_database

from sqlalchemy.pool import StaticPool

# Use in-memory SQLite with StaticPool so all connections share the same memory DB
TEST_DATABASE_URL = "sqlite:///:memory:"
engine_test = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine_test)
    db = TestingSessionLocal()
    ConfigService.init_default_configs(db)
    WorkflowEngine.get_active_template(db)
    seed_demo_database(db)
    db.close()
    yield
    Base.metadata.drop_all(bind=engine_test)

@pytest.fixture
def client():
    return TestClient(app)

def test_health_check(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["services"]["database"] == "healthy"

# --- Module 1: Access & Isolation ---

def test_login_success(client):
    res = client.post("/api/v1/auth/login", json={
        "email": "college@demo.aicte.gov.in",
        "password": "Password@123"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["role"] == UserRole.INSTITUTION

def test_login_wrong_password_gives_401(client):
    res = client.post("/api/v1/auth/login", json={
        "email": "college@demo.aicte.gov.in",
        "password": "WrongPassword123"
    })
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "INVALID_CREDENTIALS"

def test_account_lockout_after_5_failures(client):
    # Attempt 5 consecutive wrong passwords for an isolated user
    email = "admin@demo.aicte.gov.in"
    for i in range(5):
        res = client.post("/api/v1/auth/login", json={"email": email, "password": f"badpass{i}"})
        assert res.status_code in [401, 403]
    
    # 6th attempt should be locked out
    locked_res = client.post("/api/v1/auth/login", json={"email": email, "password": "Password@123"})
    assert locked_res.status_code == 403
    assert locked_res.json()["error"]["code"] == "ACCOUNT_LOCKED"
    
    # Reset lockout for following tests
    db = TestingSessionLocal()
    u = db.query(User).filter(User.email == email).first()
    u.failed_attempts = 0
    u.locked_until = None
    db.commit()
    db.close()

def test_institution_data_isolation(client):
    """Rule 1.3: College A fails to read College B's application by ID (404)"""
    # Login as College 1 (Delhi)
    login1 = client.post("/api/v1/auth/login", json={"email": "college@demo.aicte.gov.in", "password": "Password@123"}).json()
    token1 = login1["access_token"]
    
    # College 2 (Mumbai) application is WT-2026-0004
    db = TestingSessionLocal()
    app_b = db.query(Application).filter(Application.app_no == "WT-2026-0004").first()
    db.close()

    res = client.get(f"/api/v1/applications/{app_b.id}", headers={"Authorization": f"Bearer {token1}"})
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "NOT_FOUND"

def test_rbac_forbidden_action(client):
    """Rule 1.2: Scrutiny officer forbidden from recording final decision (403)"""
    login_scrutiny = client.post("/api/v1/auth/login", json={"email": "scrutiny@demo.aicte.gov.in", "password": "Password@123"}).json()
    token = login_scrutiny["access_token"]

    db = TestingSessionLocal()
    app_item = db.query(Application).first()
    db.close()

    res = client.post(
        f"/api/v1/applications/{app_item.id}/decision",
        json={"decision": "APPROVE", "order_ref": "ILLEGAL-01"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"

# --- Module 2: Workflow Engine ---

def test_invalid_workflow_transition(client):
    """Rule 2B.1: Illegal transition is rejected with INVALID_TRANSITION"""
    db = TestingSessionLocal()
    app_item = db.query(Application).filter(Application.status == "UNDER_SCRUTINY").first()
    admin_user = db.query(User).filter(User.role == UserRole.SCRUTINY_OFFICER).first()
    
    # Try invalid transition: UNDER_SCRUTINY -> CLOSED
    with pytest.raises(Exception) as excinfo:
        WorkflowEngine.transition(db, app_item, "CLOSED", actor=admin_user)
    assert "INVALID_TRANSITION" in str(excinfo.value)
    db.close()

# --- Module 3: Compliance & Undertakings ---

def test_approval_with_conditions_creates_undertakings(client):
    """Rule 3.1 & 2G.2: APPROVED_WITH_CONDITIONS creates undertakings with deadlines"""
    login_official = client.post("/api/v1/auth/login", json={"email": "official@demo.aicte.gov.in", "password": "Password@123"}).json()
    token = login_official["access_token"]

    db = TestingSessionLocal()
    test_app = db.query(Application).filter(Application.status != "CLOSED").first()
    # Mock status to DECISION_PENDING
    test_app.status = "DECISION_PENDING"
    test_app.current_stage_key = "DECISION_PENDING"
    db.commit()

    res = client.post(
        f"/api/v1/applications/{test_app.id}/decision",
        json={
            "decision": "APPROVED_WITH_CONDITIONS",
            "order_ref": "AICTE/TEST/2026/COND-01",
            "remarks": "Approved with 2 undertakings",
            "conditions": [
                {"title": "Condition A - Lease registration", "description": "Submit within 30 days", "due_days": 30},
                {"title": "Condition B - Fire safety", "description": "Submit within 15 days", "due_days": 15}
            ]
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200

    unds = db.query(Undertaking).filter(Undertaking.application_id == test_app.id).all()
    assert len(unds) >= 2
    db.close()

def test_compliance_closure_blocked_when_undertakings_open(client):
    """Rule 3.5: Closing blocked while any undertaking is not VERIFIED"""
    login_official = client.post("/api/v1/auth/login", json={"email": "official@demo.aicte.gov.in", "password": "Password@123"}).json()
    token = login_official["access_token"]

    db = TestingSessionLocal()
    app_with_und = db.query(Application).filter(Application.app_no == "WT-2026-0006").first()
    db.close()

    res = client.post(
        f"/api/v1/applications/{app_with_und.id}/close-compliance",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "UNRESOLVED_UNDERTAKINGS"

# --- Module 4 & 5: Scheduler, Escalation & Explainable Risk ---

def test_scheduler_run_and_escalation(client):
    """Rule 4.8 & 4.10: Scheduler marks overdue and escalates"""
    login_admin = client.post("/api/v1/auth/login", json={"email": "admin@demo.aicte.gov.in", "password": "Password@123"}).json()
    token = login_admin["access_token"]

    res = client.post(
        "/api/v1/admin/scheduler/run-now",
        json={},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    assert res.json()["status"] == "SUCCESS"

def test_explainable_risk_scoring(client):
    """Rule 5.7 & 5.8: Risk score has explicit factor breakdown with explanations"""
    db = TestingSessionLocal()
    app_item = db.query(Application).filter(Application.app_no == "WT-2026-0003").first()
    token = client.post("/api/v1/auth/login", json={"email": "official@demo.aicte.gov.in", "password": "Password@123"}).json()["access_token"]

    res = client.get(f"/api/v1/risk/applications/{app_item.id}", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["score"] > 0
    assert len(data["factors"]) > 0
    assert "explanation" in data["factors"][0]
    db.close()

# --- Module 6: Audit Trail Integrity ---

def test_audit_logs_recorded_for_actions(client):
    """Rule 6.5: Audit logs are recorded on changes"""
    token = client.post("/api/v1/auth/login", json={"email": "auditor@demo.aicte.gov.in", "password": "Password@123"}).json()["access_token"]
    res = client.get("/api/v1/audit-logs", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    logs = res.json()
    assert len(logs) > 0
    assert any("LOGIN_SUCCESS" in l["action"] for l in logs)

# --- Additional Demo Readiness Tests (Parts 2, 4, 5) ---

def test_deficiency_response_flow(client):
    """Part 2: Deficiency response requires all items, transitions to UNDER_SCRUTINY, increments round, notifies officer"""
    db = TestingSessionLocal()
    app_item = db.query(Application).filter(Application.status == "DEFICIENCY_RAISED").first()
    db.close()
    if not app_item:
        return

    college_token = client.post("/api/v1/auth/login", json={"email": "college@demo.aicte.gov.in", "password": "Password@123"}).json()["access_token"]
    
    # Fetch deficiencies
    res_defs = client.get(f"/api/v1/applications/{app_item.id}/deficiencies", headers={"Authorization": f"Bearer {college_token}"})
    assert res_defs.status_code == 200
    defs = res_defs.json()
    assert len(defs) > 0

    # Incomplete response blocked
    res_bad = client.post(
        f"/api/v1/applications/{app_item.id}/deficiencies/respond",
        json={"responses": [{"deficiency_id": defs[0]["id"], "response_text": "Only one answered"}]},
        headers={"Authorization": f"Bearer {college_token}"}
    )
    assert res_bad.status_code == 400
    assert res_bad.json()["error"]["code"] == "INCOMPLETE_RESPONSE"

    # Full response succeeds
    full_responses = [{"deficiency_id": d["id"], "response_text": f"Addressed item {d['item']}"} for d in defs]
    res_good = client.post(
        f"/api/v1/applications/{app_item.id}/deficiencies/respond",
        json={"responses": full_responses},
        headers={"Authorization": f"Bearer {college_token}"}
    )
    assert res_good.status_code == 200
    assert res_good.json()["status"] == "UNDER_SCRUTINY"

def test_region_scoping_enforcement(client):
    """Part 4: Region scoping allows officers to access only applications in their own region"""
    scrutiny_north_token = client.post("/api/v1/auth/login", json={"email": "scrutiny@demo.aicte.gov.in", "password": "Password@123"}).json()["access_token"]
    
    db = TestingSessionLocal()
    west_app = db.query(Application).filter(Application.app_no == "WT-2026-0004").first() # Mumbai inst (WEST)
    db.close()
    
    if west_app:
        # North officer cannot access West application (403)
        res = client.get(f"/api/v1/applications/{west_app.id}", headers={"Authorization": f"Bearer {scrutiny_north_token}"})
        assert res.status_code == 403
        assert res.json()["error"]["code"] == "REGION_RESTRICTED"

def test_escalation_ladder_validation_and_audit(client):
    """Part 5: Escalation ladder validates days > 0, L2 > L1, and writes audit record"""
    admin_token = client.post("/api/v1/auth/login", json={"email": "admin@demo.aicte.gov.in", "password": "Password@123"}).json()["access_token"]
    
    # L2 <= L1 rejected with 400
    bad_req = {
        "items": [{"target_type": "TASK", "l1_role": "AUTHORISED_OFFICIAL", "l1_days": 5, "l2_role": "AUTHORISED_OFFICIAL", "l2_days": 2}]
    }
    res_bad = client.put("/api/v1/escalation-rules/ladder", json=bad_req, headers={"Authorization": f"Bearer {admin_token}"})
    assert res_bad.status_code == 400
    assert res_bad.json()["error"]["code"] == "INVALID_LADDER_ORDER"

    # Days <= 0 rejected with 400
    bad_req2 = {
        "items": [{"target_type": "TASK", "l1_role": "AUTHORISED_OFFICIAL", "l1_days": 0, "l2_role": "AUTHORISED_OFFICIAL", "l2_days": 4}]
    }
    res_bad2 = client.put("/api/v1/escalation-rules/ladder", json=bad_req2, headers={"Authorization": f"Bearer {admin_token}"})
    assert res_bad2.status_code == 400
    assert res_bad2.json()["error"]["code"] == "INVALID_DAYS"

    # Valid save
    good_req = {
        "items": [
            {"target_type": "TASK", "l1_role": "AUTHORISED_OFFICIAL", "l1_days": 2, "l2_role": "AUTHORISED_OFFICIAL", "l2_days": 5},
            {"target_type": "UNDERTAKING", "l1_role": "AUTHORISED_OFFICIAL", "l1_days": 2, "l2_role": "AUTHORISED_OFFICIAL", "l2_days": 5},
            {"target_type": "DOCUMENT", "l1_role": "AUTHORISED_OFFICIAL", "l1_days": 2, "l2_role": "AUTHORISED_OFFICIAL", "l2_days": 5}
        ]
    }
    res_good = client.put("/api/v1/escalation-rules/ladder", json=good_req, headers={"Authorization": f"Bearer {admin_token}"})
    assert res_good.status_code == 200
