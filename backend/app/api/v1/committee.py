from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.committee import CommitteeReview
from app.models.user import User, UserRole
from app.schemas.committee import CommitteeReviewResponse, CommitteeReviewSubmit
from app.services.committee_service import CommitteeService

router = APIRouter(prefix="/committee-reviews", tags=["Committee Reviews"])

@router.get("", response_model=List[CommitteeReviewResponse])
def list_committee_reviews(
    application_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(CommitteeReview)
    if application_id:
        query = query.filter(CommitteeReview.application_id == application_id)
    if current_user.role == UserRole.COMMITTEE_MEMBER:
        query = query.filter(CommitteeReview.reviewer_id == current_user.id)
    reviews = query.order_by(CommitteeReview.created_at.desc()).all()
    
    res = []
    for r in reviews:
        reviewer = db.query(User).filter(User.id == r.reviewer_id).first()
        res.append(CommitteeReviewResponse(
            id=r.id,
            application_id=r.application_id,
            committee_type=r.committee_type,
            reviewer_id=r.reviewer_id,
            reviewer_name=reviewer.full_name if reviewer else "Reviewer",
            status=r.status,
            recommendation=r.recommendation,
            remarks=r.remarks,
            due_at=r.due_at,
            created_at=r.created_at
        ))
    return res

@router.post("/{id}/submit", response_model=CommitteeReviewResponse)
def submit_committee_recommendation(
    id: str,
    req: CommitteeReviewSubmit,
    current_user: User = Depends(require_role([UserRole.COMMITTEE_MEMBER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    r = CommitteeService.submit_recommendation(db, id, req, current_user)
    reviewer = db.query(User).filter(User.id == r.reviewer_id).first()
    return CommitteeReviewResponse(
        id=r.id,
        application_id=r.application_id,
        committee_type=r.committee_type,
        reviewer_id=r.reviewer_id,
        reviewer_name=reviewer.full_name if reviewer else "Reviewer",
        status=r.status,
        recommendation=r.recommendation,
        remarks=r.remarks,
        due_at=r.due_at,
        created_at=r.created_at
    )
