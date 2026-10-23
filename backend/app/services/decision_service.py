from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import utcnow
from app.core.audit import log_audit
from app.models.workflow import Application
from app.models.decision import Decision
from app.models.compliance import Undertaking
from app.models.user import User, UserRole
from app.workflow.engine import WorkflowEngine
from app.schemas.decision import DecisionCreate

class DecisionService:
    @staticmethod
    def record_decision(
        db: Session,
        application_id: str,
        data: DecisionCreate,
        official: User
    ) -> Decision:
        if official.role not in [UserRole.AUTHORISED_OFFICIAL, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "Only Authorised Officials can record final decisions"}
            )

        app = db.query(Application).filter(Application.id == application_id).first()
        if not app:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Application not found"})

        now = utcnow()
        decision = Decision(
            application_id=app.id,
            decision=data.decision,
            decided_by=official.id,
            order_ref=data.order_ref,
            remarks=data.remarks,
            decided_at=now
        )
        db.add(decision)
        db.commit()
        db.refresh(decision)

        # 3.1 & 2G.2: Convert conditions to undertakings if APPROVED_WITH_CONDITIONS
        if data.decision == "APPROVED_WITH_CONDITIONS":
            for cond in data.conditions:
                due = now + timedelta(days=cond.due_days)
                undertaking = Undertaking(
                    application_id=app.id,
                    institution_id=app.institution_id,
                    title=cond.title,
                    description=cond.description,
                    due_at=due,
                    status="PENDING"
                )
                db.add(undertaking)
            db.commit()

        app.decided_at = now
        # Advance workflow to final stage
        WorkflowEngine.transition(
            db,
            app,
            data.decision,
            actor=official,
            outcome=f"Decision recorded: {data.decision} (Ref: {data.order_ref})"
        )

        log_audit(
            db=db,
            action="RECORD_DECISION",
            entity_type="APPLICATION",
            entity_id=app.id,
            actor_id=official.id,
            after_state={"decision": data.decision, "order_ref": data.order_ref}
        )
        return decision
