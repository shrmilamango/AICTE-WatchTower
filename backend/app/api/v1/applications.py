from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db, utcnow
from app.core.deps import get_current_user, require_role
from app.models.workflow import Application, Task
from app.models.institution import Institution
from app.models.user import User, UserRole
from app.models.risk import RiskScore
from app.schemas.workflow import (
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationResponse,
    TimelineItem
)
from app.schemas.scrutiny import ScrutinyReviewCreate, DeficienciesRespondRequest
from app.schemas.evc import EvcScheduleRequest
from app.schemas.committee import CommitteeAssignRequest
from app.schemas.decision import DecisionCreate
from app.services.workflow_service import WorkflowService
from app.services.scrutiny_service import ScrutinyService
from app.services.evc_service import EvcService
from app.services.committee_service import CommitteeService
from app.services.decision_service import DecisionService
from app.services.compliance_service import ComplianceService

router = APIRouter(prefix="/applications", tags=["Applications"])

def enrich_app_response(app: Application, db: Session) -> ApplicationResponse:
    inst = db.query(Institution).filter(Institution.id == app.institution_id).first()
    owner = db.query(User).filter(User.id == app.current_owner_id).first() if app.current_owner_id else None
    risk = db.query(RiskScore).filter(RiskScore.application_id == app.id).first()
    
    # Days pending in current stage
    days_pending = (utcnow() - app.submitted_at).days if app.submitted_at else 0

    return ApplicationResponse(
        id=app.id,
        app_no=app.app_no,
        institution_id=app.institution_id,
        template_id=app.template_id,
        programme=app.programme,
        academic_year=app.academic_year,
        form_data=app.form_data or {},
        status=app.status,
        current_stage_key=app.current_stage_key,
        current_owner_id=app.current_owner_id,
        submitted_at=app.submitted_at,
        decided_at=app.decided_at,
        created_at=app.created_at,
        updated_at=app.updated_at,
        institution_name=inst.name if inst else "Unknown",
        owner_name=owner.full_name if owner else None,
        pending_with=WorkflowService.get_pending_with_display(app, owner),
        days_pending=days_pending,
        risk_level=risk.level if risk else "LOW",
        risk_score=risk.score if risk else 0
    )

@router.get("", response_model=List[ApplicationResponse])
def list_applications(
    status: Optional[str] = None,
    programme: Optional[str] = None,
    region: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Application)
    
    # Rule 1.3: Institution isolation
    if current_user.role == UserRole.INSTITUTION:
        query = query.filter(Application.institution_id == current_user.institution_id)
    elif region:
        query = query.join(Institution, Application.institution_id == Institution.id).filter(Institution.region == region)

    if status:
        query = query.filter(Application.status == status)
    if programme:
        query = query.filter(Application.programme == programme)

    apps = query.order_by(Application.created_at.desc()).all()
    return [enrich_app_response(a, db) for a in apps]

@router.post("", response_model=ApplicationResponse, dependencies=[Depends(require_role([UserRole.INSTITUTION]))])
def create_application_draft(
    req: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.institution_id:
        raise HTTPException(status_code=400, detail={"code": "NO_INSTITUTION", "message": "User not linked to an institution"})
    app = WorkflowService.create_draft(db, current_user.institution_id, req, current_user)
    return enrich_app_response(app, db)

@router.get("/{id}", response_model=ApplicationResponse)
def get_application(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Application not found"})
    if current_user.role == UserRole.INSTITUTION and app.institution_id != current_user.institution_id:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Application not found"})
    return enrich_app_response(app, db)

@router.put("/{id}", response_model=ApplicationResponse)
def update_application_draft(
    id: str,
    req: ApplicationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    app = WorkflowService.update_draft(db, id, req, current_user)
    return enrich_app_response(app, db)

@router.post("/{id}/submit", response_model=ApplicationResponse)
def submit_application(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    app = WorkflowService.submit_application(db, id, current_user)
    return enrich_app_response(app, db)

@router.get("/{id}/timeline", response_model=List[TimelineItem])
def get_application_timeline(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Application not found"})
    if current_user.role == UserRole.INSTITUTION and app.institution_id != current_user.institution_id:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Application not found"})
    return WorkflowService.get_timeline(db, id)

# --- Workflow Stage Action Sub-endpoints ---

@router.post("/{id}/scrutiny")
def submit_scrutiny(
    id: str,
    req: ScrutinyReviewCreate,
    current_user: User = Depends(require_role([UserRole.SCRUTINY_OFFICER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    rev = ScrutinyService.review_application(db, id, req, current_user)
    return {"status": "SUCCESS", "review_id": rev.id, "outcome": rev.outcome}

@router.post("/{id}/deficiencies/respond")
def respond_deficiencies(
    id: str,
    req: DeficienciesRespondRequest,
    current_user: User = Depends(require_role([UserRole.INSTITUTION])),
    db: Session = Depends(get_db)
):
    app = ScrutinyService.respond_deficiencies(db, id, req, current_user)
    return enrich_app_response(app, db)

@router.post("/{id}/evc/schedule")
def schedule_evc(
    id: str,
    req: EvcScheduleRequest,
    current_user: User = Depends(require_role([UserRole.EVC_COORDINATOR, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    visit = EvcService.schedule_visit(db, id, req, current_user)
    return {"status": "SUCCESS", "visit_id": visit.id, "scheduled_date": visit.scheduled_date}

@router.post("/{id}/committee/assign")
def assign_committee(
    id: str,
    req: CommitteeAssignRequest,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.AUTHORISED_OFFICIAL])),
    db: Session = Depends(get_db)
):
    reviews = CommitteeService.assign_committee(db, id, req, current_user)
    return {"status": "SUCCESS", "assigned_reviews": len(reviews)}

@router.post("/{id}/decision")
def record_decision(
    id: str,
    req: DecisionCreate,
    current_user: User = Depends(require_role([UserRole.AUTHORISED_OFFICIAL, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    dec = DecisionService.record_decision(db, id, req, current_user)
    return {"status": "SUCCESS", "decision_id": dec.id, "decision": dec.decision}

@router.post("/{id}/close-compliance")
def close_compliance(
    id: str,
    current_user: User = Depends(require_role([UserRole.AUTHORISED_OFFICIAL, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    app = ComplianceService.close_application_compliance(db, id, current_user)
    return enrich_app_response(app, db)
