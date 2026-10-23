from datetime import datetime, timedelta
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import utcnow
from app.core.audit import log_audit
from app.models.workflow import Application
from app.models.scrutiny import ScrutinyReview, Deficiency
from app.models.user import User, UserRole
from app.workflow.engine import WorkflowEngine
from app.schemas.scrutiny import ScrutinyReviewCreate, DeficienciesRespondRequest

class ScrutinyService:
    @staticmethod
    def review_application(
        db: Session,
        application_id: str,
        data: ScrutinyReviewCreate,
        officer: User
    ) -> ScrutinyReview:
        app = db.query(Application).filter(Application.id == application_id).first()
        if not app:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Application not found"})

        # Get existing round count
        last_review = db.query(ScrutinyReview).filter(
            ScrutinyReview.application_id == application_id
        ).order_by(ScrutinyReview.round_no.desc()).first()
        current_round = (last_review.round_no + 1) if last_review else 1

        if data.outcome == "DEFICIENT" and not data.deficiencies:
            raise HTTPException(
                status_code=400,
                detail={"code": "DEFICIENCIES_REQUIRED", "message": "At least one deficiency item must be specified for DEFICIENT outcome"}
            )

        review = ScrutinyReview(
            application_id=app.id,
            reviewer_id=officer.id,
            round_no=current_round,
            outcome=data.outcome,
            remarks=data.remarks
        )
        db.add(review)
        db.commit()
        db.refresh(review)

        now = utcnow()
        if data.outcome == "DEFICIENT":
            for d in data.deficiencies:
                due = now + timedelta(days=d.due_days)
                deficiency = Deficiency(
                    review_id=review.id,
                    item=d.item,
                    description=d.description,
                    status="OPEN",
                    due_at=due
                )
                db.add(deficiency)
            db.commit()

            # Transition application to DEFICIENCY_RAISED
            WorkflowEngine.transition(
                db,
                app,
                "DEFICIENCY_RAISED",
                actor=officer,
                outcome=f"Deficiencies raised in Scrutiny Round {current_round}"
            )
        else:
            # PASS - check whether EVC is required or proceed to committee
            # For demonstration, standard technical programmes require EVC
            next_stage = "EVC_REQUIRED" if app.programme in ["Engineering & Technology", "Pharmacy", "Architecture", "Engineering"] else "COMMITTEE_REVIEW"
            WorkflowEngine.transition(
                db,
                app,
                next_stage,
                actor=officer,
                outcome=f"Passed Scrutiny Round {current_round}"
            )

        log_audit(
            db=db,
            action="SCRUTINY_REVIEW",
            entity_type="SCRUTINY_REVIEW",
            entity_id=review.id,
            actor_id=officer.id,
            after_state={"outcome": data.outcome, "round": current_round}
        )
        return review

    @staticmethod
    def respond_deficiencies(
        db: Session,
        application_id: str,
        data: DeficienciesRespondRequest,
        institution_user: User
    ) -> Application:
        app = db.query(Application).filter(Application.id == application_id).first()
        if not app:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Application not found"})

        # Get latest review with open deficiencies
        last_review = db.query(ScrutinyReview).filter(
            ScrutinyReview.application_id == application_id,
            ScrutinyReview.outcome == "DEFICIENT"
        ).order_by(ScrutinyReview.round_no.desc()).first()

        if not last_review:
            raise HTTPException(status_code=400, detail={"code": "NO_DEFICIENCIES", "message": "No active deficiency review found"})

        open_defs = db.query(Deficiency).filter(
            Deficiency.review_id == last_review.id,
            Deficiency.status == "OPEN"
        ).all()

        submitted_ids = {r.deficiency_id for r in data.responses}
        for d in open_defs:
            if d.id not in submitted_ids:
                raise HTTPException(
                    status_code=400,
                    detail={"code": "INCOMPLETE_RESPONSE", "message": f"Must respond to all deficiency items. Missing item: '{d.item}'"}
                )

        now = utcnow()
        for r in data.responses:
            d = next((item for item in open_defs if item.id == r.deficiency_id), None)
            if d:
                d.response_text = r.response_text
                d.status = "RESOLVED"
                d.resolved_at = now

        db.commit()

        # Resubmit back to the same scrutiny officer
        WorkflowEngine.transition(
            db,
            app,
            "RESUBMITTED",
            actor=institution_user,
            outcome="Corrections submitted by institution",
            force_owner_id=last_review.reviewer_id
        )

        WorkflowEngine.transition(
            db,
            app,
            "UNDER_SCRUTINY",
            actor=institution_user,
            outcome="Under re-scrutiny by same officer",
            force_owner_id=last_review.reviewer_id
        )

        log_audit(
            db=db,
            action="DEFICIENCY_RESUBMISSION",
            entity_type="APPLICATION",
            entity_id=app.id,
            actor_id=institution_user.id
        )
        return app
