from datetime import datetime, timedelta
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import utcnow
from app.core.audit import log_audit
from app.models.workflow import Application, Task
from app.models.committee import CommitteeReview
from app.models.user import User, UserRole
from app.workflow.engine import WorkflowEngine
from app.schemas.committee import CommitteeAssignRequest, CommitteeReviewSubmit

class CommitteeService:
    @staticmethod
    def assign_committee(
        db: Session,
        application_id: str,
        data: CommitteeAssignRequest,
        actor: User
    ) -> List[CommitteeReview]:
        app = db.query(Application).filter(Application.id == application_id).first()
        if not app:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Application not found"})

        reviews = []
        due = utcnow() + timedelta(days=data.due_days)
        for uid in data.reviewer_ids:
            rev = CommitteeReview(
                application_id=app.id,
                committee_type=data.committee_type,
                reviewer_id=uid,
                status="PENDING",
                due_at=due
            )
            db.add(rev)
            reviews.append(rev)

            # Create individual task for each reviewer
            task = Task(
                application_id=app.id,
                type=f"COMMITTEE_{data.committee_type}",
                assigned_to=uid,
                role=UserRole.COMMITTEE_MEMBER,
                due_at=due,
                status="OPEN"
            )
            db.add(task)

        db.commit()
        for r in reviews:
            db.refresh(r)

        log_audit(
            db=db,
            action="ASSIGN_COMMITTEE",
            entity_type="APPLICATION",
            entity_id=app.id,
            actor_id=actor.id,
            after_state={"committee_type": data.committee_type, "reviewers_count": len(data.reviewer_ids)}
        )
        return reviews

    @staticmethod
    def submit_recommendation(
        db: Session,
        review_id: str,
        data: CommitteeReviewSubmit,
        reviewer: User
    ) -> CommitteeReview:
        review = db.query(CommitteeReview).filter(CommitteeReview.id == review_id).first()
        if not review:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Committee review item not found"})

        if review.reviewer_id != reviewer.id and reviewer.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "Not assigned to this review"})

        review.recommendation = data.recommendation
        review.remarks = data.remarks
        review.status = "COMPLETED"
        db.commit()
        db.refresh(review)

        # Mark corresponding task DONE
        db.query(Task).filter(
            Task.application_id == review.application_id,
            Task.assigned_to == reviewer.id,
            Task.status == "OPEN"
        ).update({"status": "DONE"})
        db.commit()

        # Check if all reviews for this application are complete
        pending = db.query(CommitteeReview).filter(
            CommitteeReview.application_id == review.application_id,
            CommitteeReview.status == "PENDING"
        ).count()

        if pending == 0:
            app = db.query(Application).filter(Application.id == review.application_id).first()
            if app and app.status == "COMMITTEE_REVIEW":
                WorkflowEngine.transition(
                    db,
                    app,
                    "DECISION_PENDING",
                    actor=reviewer,
                    outcome="All committee recommendations submitted"
                )

        log_audit(
            db=db,
            action="COMMITTEE_RECOMMENDATION",
            entity_type="COMMITTEE_REVIEW",
            entity_id=review.id,
            actor_id=reviewer.id,
            after_state={"recommendation": data.recommendation}
        )
        return review
