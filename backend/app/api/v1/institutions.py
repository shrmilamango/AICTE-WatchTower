from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, require_role, verify_institution_access
from app.models.user import User, UserRole
from app.schemas.institution import InstitutionResponse, InstitutionCreate, InstitutionUpdate, InstitutionSummary
from app.services.institution_service import InstitutionService

router = APIRouter(prefix="/institutions", tags=["Institutions"])

@router.get("", response_model=List[InstitutionResponse])
def list_institutions(
    region: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role == UserRole.INSTITUTION:
        if current_user.institution_id:
            return [InstitutionService.get_by_id(db, current_user.institution_id)]
        return []
    return InstitutionService.get_all(db, region=region)

@router.post("", response_model=InstitutionResponse, dependencies=[Depends(require_role([UserRole.ADMIN, UserRole.AUTHORISED_OFFICIAL]))])
def create_institution(
    req: InstitutionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return InstitutionService.create(db, req, actor_id=current_user.id)

@router.get("/{id}", response_model=InstitutionResponse)
def get_institution(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_institution_access(id, current_user)
    return InstitutionService.get_by_id(db, id)

@router.patch("/{id}", response_model=InstitutionResponse)
def update_institution(
    id: str,
    req: InstitutionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_institution_access(id, current_user)
    return InstitutionService.update(db, id, req, actor_id=current_user.id)

@router.get("/{id}/summary", response_model=InstitutionSummary)
def get_institution_summary(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_institution_access(id, current_user)
    return InstitutionService.get_summary(db, id)
