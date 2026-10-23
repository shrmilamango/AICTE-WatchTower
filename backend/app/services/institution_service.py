from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core.audit import log_audit
from app.models.institution import Institution
from app.models.workflow import Application
from app.models.scrutiny import ScrutinyReview, Deficiency
from app.models.compliance import Undertaking, Document
from app.schemas.institution import InstitutionCreate, InstitutionUpdate, InstitutionSummary

class InstitutionService:
    @staticmethod
    def get_all(db: Session, region: Optional[str] = None) -> List[Institution]:
        query = db.query(Institution)
        if region:
            query = query.filter(Institution.region == region)
        return query.order_name() if hasattr(query, 'order_name') else query.all()

    @staticmethod
    def get_by_id(db: Session, institution_id: str) -> Institution:
        inst = db.query(Institution).filter(Institution.id == institution_id).first()
        if not inst:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "INSTITUTION_NOT_FOUND", "message": "Institution not found"}
            )
        return inst

    @staticmethod
    def create(db: Session, data: InstitutionCreate, actor_id: Optional[str] = None) -> Institution:
        existing = db.query(Institution).filter(Institution.aicte_code == data.aicte_code).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "DUPLICATE_AICTE_CODE", "message": f"AICTE code '{data.aicte_code}' already exists"}
            )
        inst = Institution(**data.model_dump())
        db.add(inst)
        db.commit()
        db.refresh(inst)
        
        log_audit(
            db=db,
            action="CREATE_INSTITUTION",
            entity_type="INSTITUTION",
            entity_id=inst.id,
            actor_id=actor_id,
            after_state=data.model_dump()
        )
        return inst

    @staticmethod
    def update(db: Session, institution_id: str, data: InstitutionUpdate, actor_id: Optional[str] = None) -> Institution:
        inst = InstitutionService.get_by_id(db, institution_id)
        before = {c.name: getattr(inst, c.name) for c in inst.__table__.columns}
        
        update_dict = data.model_dump(exclude_unset=True)
        for key, val in update_dict.items():
            setattr(inst, key, val)
        db.commit()
        db.refresh(inst)
        
        log_audit(
            db=db,
            action="UPDATE_INSTITUTION",
            entity_type="INSTITUTION",
            entity_id=inst.id,
            actor_id=actor_id,
            before_state=before,
            after_state=update_dict
        )
        return inst

    @staticmethod
    def get_summary(db: Session, institution_id: str) -> dict:
        inst = InstitutionService.get_by_id(db, institution_id)
        total_apps = db.query(Application).filter(Application.institution_id == institution_id).count()
        
        # open deficiencies
        open_defs = db.query(Deficiency).join(ScrutinyReview, Deficiency.review_id == ScrutinyReview.id)\
            .join(Application, ScrutinyReview.application_id == Application.id)\
            .filter(Application.institution_id == institution_id, Deficiency.status == "OPEN").count()
            
        # pending undertakings
        pending_unds = db.query(Undertaking).filter(
            Undertaking.institution_id == institution_id,
            Undertaking.status.in_(["PENDING", "OVERDUE"])
        ).count()
        
        # expiring documents
        exp_docs = db.query(Document).filter(
            Document.institution_id == institution_id,
            Document.status.in_(["EXPIRING", "EXPIRED"])
        ).count()
        
        return {
            "institution": inst,
            "total_applications": total_apps,
            "open_deficiencies": open_defs,
            "pending_undertakings": pending_unds,
            "expiring_documents": exp_docs
        }
