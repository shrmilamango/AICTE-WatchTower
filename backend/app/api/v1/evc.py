from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db, utcnow
from app.core.deps import get_current_user, require_role
from app.models.evc import EvcVisit
from app.models.workflow import Application
from app.models.institution import Institution
from app.models.user import User, UserRole
from app.schemas.evc import EvcResponse, EvcCompleteRequest, EvcScheduleRequest
from app.services.evc_service import EvcService

router = APIRouter(prefix="/evc", tags=["EVC Inspection"])

def enrich_evc_response(v: EvcVisit, db: Session) -> EvcResponse:
    app = db.query(Application).filter(Application.id == v.application_id).first()
    inst = db.query(Institution).filter(Institution.id == app.institution_id).first() if app else None
    coord = db.query(User).filter(User.id == v.coordinator_id).first() if v.coordinator_id else None
    
    # 2E.5 Unscheduled alert: visit still REQUIRED after target_date
    now = utcnow()
    is_unscheduled = (v.status == "REQUIRED" and v.target_date and v.target_date < now)

    return EvcResponse(
        id=v.id,
        application_id=v.application_id,
        app_no=app.app_no if app else None,
        institution_name=inst.name if inst else "Unknown",
        status=v.status,
        target_date=v.target_date,
        scheduled_date=v.scheduled_date,
        members=v.members or [],
        coordinator_id=v.coordinator_id,
        coordinator_name=coord.full_name if coord else "Unassigned",
        report_document_id=v.report_document_id,
        remarks=v.remarks,
        created_at=v.created_at,
        is_unscheduled_alert=is_unscheduled
    )

@router.get("", response_model=List[EvcResponse])
def list_evc_visits(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    visits = EvcService.get_all(db, status_filter=status)
    return [enrich_evc_response(v, db) for v in visits]

@router.patch("/{id}", response_model=EvcResponse)
def update_evc_schedule(
    id: str,
    req: EvcScheduleRequest,
    current_user: User = Depends(require_role([UserRole.EVC_COORDINATOR, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    visit = db.query(EvcVisit).filter(EvcVisit.id == id).first()
    if not visit:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "EVC visit not found"})
    v = EvcService.schedule_visit(db, visit.application_id, req, current_user)
    return enrich_evc_response(v, db)

@router.post("/{id}/complete", response_model=EvcResponse)
def complete_evc_visit(
    id: str,
    req: EvcCompleteRequest,
    current_user: User = Depends(require_role([UserRole.EVC_COORDINATOR, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    v = EvcService.complete_visit(db, id, req, current_user)
    return enrich_evc_response(v, db)
