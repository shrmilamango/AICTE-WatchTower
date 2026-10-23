from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.risk import RiskScore
from app.models.workflow import Application
from app.models.institution import Institution
from app.models.user import User, UserRole
from app.schemas.alert import RiskScoreResponse
from app.services.risk_service import RiskService

router = APIRouter(prefix="/risk", tags=["Explainable Risk Scoring"])

def enrich_risk_response(r: RiskScore, db: Session) -> RiskScoreResponse:
    app = db.query(Application).filter(Application.id == r.application_id).first()
    inst = db.query(Institution).filter(Institution.id == app.institution_id).first() if app else None

    return RiskScoreResponse(
        id=r.id,
        application_id=r.application_id,
        app_no=app.app_no if app else "Unknown",
        institution_name=inst.name if inst else "Unknown",
        score=r.score,
        level=r.level,
        factors=r.factors or [],
        computed_at=r.computed_at
    )

@router.get("/applications", response_model=List[RiskScoreResponse])
def get_risk_applications(
    level: Optional[str] = None, # LOW, MEDIUM, HIGH
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rule 5.8: High-risk list with visible 'why' text reasons"""
    query = db.query(RiskScore).join(Application, RiskScore.application_id == Application.id)
    if current_user.role == UserRole.INSTITUTION:
        query = query.filter(Application.institution_id == current_user.institution_id)
    if level:
        query = query.filter(RiskScore.level == level)
    
    # Sort descending by risk score
    risks = query.order_by(RiskScore.score.desc()).all()
    return [enrich_risk_response(r, db) for r in risks]

@router.get("/applications/{id}", response_model=RiskScoreResponse)
def get_application_risk(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Application not found"})
        
    risk = db.query(RiskScore).filter(RiskScore.application_id == id).first()
    if not risk:
        risk = RiskService.compute_risk(db, app)
    return enrich_risk_response(risk, db)

@router.post("/recompute")
def recompute_risk_scores(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    count = RiskService.recompute_all(db)
    return {"status": "SUCCESS", "recomputed_applications": count}
