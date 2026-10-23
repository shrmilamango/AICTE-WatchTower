from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import utcnow
from app.core.audit import log_audit
from app.models.workflow import Application
from app.models.evc import EvcVisit
from app.models.user import User, UserRole
from app.workflow.engine import WorkflowEngine
from app.schemas.evc import EvcScheduleRequest, EvcCompleteRequest

class EvcService:
    @staticmethod
    def mark_required(db: Session, application_id: str, actor: User, target_days: int = 14) -> EvcVisit:
        app = db.query(Application).filter(Application.id == application_id).first()
        if not app:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Application not found"})

        visit = EvcVisit(
            application_id=app.id,
            status="REQUIRED",
            target_date=utcnow() + timedelta(days=target_days),
            coordinator_id=actor.id if actor.role == UserRole.EVC_COORDINATOR else None
        )
        db.add(visit)
        db.commit()
        db.refresh(visit)

        WorkflowEngine.transition(
            db,
            app,
            "EVC_REQUIRED",
            actor=actor,
            outcome="Marked for Expert Visit Committee (EVC) Inspection"
        )
        return visit

    @staticmethod
    def schedule_visit(
        db: Session,
        application_id: str,
        data: EvcScheduleRequest,
        coordinator: User
    ) -> EvcVisit:
        app = db.query(Application).filter(Application.id == application_id).first()
        if not app:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Application not found"})

        visit = db.query(EvcVisit).filter(
            EvcVisit.application_id == application_id,
            EvcVisit.status.in_(["REQUIRED", "SCHEDULED"])
        ).order_by(EvcVisit.created_at.desc()).first()

        if not visit:
            visit = EvcVisit(
                application_id=application_id,
                status="REQUIRED",
                coordinator_id=coordinator.id
            )
            db.add(visit)

        # Validate date is in future (or allow for demo flexibility if needed, but check)
        visit.scheduled_date = data.scheduled_date
        visit.members = [m.model_dump() for m in data.members]
        visit.remarks = data.remarks
        visit.status = "SCHEDULED"
        visit.coordinator_id = coordinator.id
        db.commit()
        db.refresh(visit)

        WorkflowEngine.transition(
            db,
            app,
            "EVC_SCHEDULED",
            actor=coordinator,
            outcome=f"EVC Inspection scheduled for {data.scheduled_date.strftime('%Y-%m-%d')}"
        )

        log_audit(
            db=db,
            action="SCHEDULE_EVC",
            entity_type="EVC_VISIT",
            entity_id=visit.id,
            actor_id=coordinator.id,
            after_state={"scheduled_date": str(data.scheduled_date), "members_count": len(data.members)}
        )
        return visit

    @staticmethod
    def complete_visit(
        db: Session,
        evc_id: str,
        data: EvcCompleteRequest,
        coordinator: User
    ) -> EvcVisit:
        visit = db.query(EvcVisit).filter(EvcVisit.id == evc_id).first()
        if not visit:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "EVC visit not found"})

        app = db.query(Application).filter(Application.id == visit.application_id).first()

        visit.status = "COMPLETED"
        visit.report_document_id = data.report_document_id
        visit.remarks = data.remarks
        db.commit()
        db.refresh(visit)

        # Transition application to EVC_COMPLETED then COMMITTEE_REVIEW
        WorkflowEngine.transition(
            db,
            app,
            "EVC_COMPLETED",
            actor=coordinator,
            outcome="EVC inspection report submitted"
        )

        WorkflowEngine.transition(
            db,
            app,
            "COMMITTEE_REVIEW",
            actor=coordinator,
            outcome="Proceeded to SAC/SHC Committee review"
        )

        log_audit(
            db=db,
            action="COMPLETE_EVC",
            entity_type="EVC_VISIT",
            entity_id=visit.id,
            actor_id=coordinator.id,
            after_state={"outcome": data.outcome}
        )
        return visit

    @staticmethod
    def get_all(db: Session, status_filter: Optional[str] = None) -> List[EvcVisit]:
        query = db.query(EvcVisit)
        if status_filter:
            query = query.filter(EvcVisit.status == status_filter)
        return query.order_by(EvcVisit.created_at.desc()).all()
