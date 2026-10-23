from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.core.security import hash_password
from app.core.audit import log_audit
from app.models.user import User, UserRole
from app.schemas.user import UserResponse, UserCreate, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("", response_model=List[UserResponse])
def list_users(
    role: Optional[str] = None,
    region: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if region:
        query = query.filter(User.region == region)
    return query.order_by(User.full_name.asc()).all()

@router.post("", response_model=UserResponse, dependencies=[Depends(require_role([UserRole.ADMIN]))])
def create_user(
    req: UserCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing = db.query(User).filter(User.email == req.email.lower().strip()).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail={"code": "DUPLICATE_EMAIL", "message": "Email already registered"}
        )
    user = User(
        email=req.email.lower().strip(),
        password_hash=hash_password(req.password),
        full_name=req.full_name,
        role=req.role,
        institution_id=req.institution_id,
        region=req.region,
        is_active=req.is_active
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_audit(
        db=db,
        action="CREATE_USER",
        entity_type="USER",
        entity_id=user.id,
        actor_id=current_user.id,
        after_state={"email": user.email, "role": user.role}
    )
    return user

@router.patch("/{id}", response_model=UserResponse, dependencies=[Depends(require_role([UserRole.ADMIN]))])
def update_user(
    id: str,
    req: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "User not found"})
    
    before = {"role": user.role, "full_name": user.full_name, "is_active": user.is_active}
    update_data = req.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(user, k, v)
    db.commit()
    db.refresh(user)

    log_audit(
        db=db,
        action="UPDATE_USER",
        entity_type="USER",
        entity_id=user.id,
        actor_id=current_user.id,
        before_state=before,
        after_state=update_data
    )
    return user

@router.patch("/{id}/deactivate", response_model=UserResponse, dependencies=[Depends(require_role([UserRole.ADMIN]))])
def deactivate_user(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.services.auth_service import AuthService
    return AuthService.deactivate_user(db, id, current_user)
