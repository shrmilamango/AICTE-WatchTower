from datetime import datetime, timedelta
from typing import Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import utcnow
from app.core.audit import log_audit
from app.models.workflow import (
    WorkflowTemplate,
    WorkflowStage,
    Application,
    ApplicationStageHistory,
    Task
)
from app.models.institution import Institution
from app.models.user import User, UserRole

class WorkflowEngine:
    @staticmethod
    def get_active_template(db: Session) -> WorkflowTemplate:
        template = db.query(WorkflowTemplate).filter(WorkflowTemplate.is_active == True).first()
        if not template:
            # Fallback to create default template if none exists
            template = WorkflowEngine.init_default_template(db)
        return template

    @staticmethod
    def init_default_template(db: Session) -> WorkflowTemplate:
        template = WorkflowTemplate(
            name="AICTE Approval Process Handbook (Standard)",
            version=1,
            is_active=True,
            description="Default workflow mapped to AICTE Approval Process Handbook"
        )
        db.add(template)
        db.commit()
        db.refresh(template)

        # Standard stages defined in section 1.6:
        # DRAFT -> SUBMITTED -> UNDER_SCRUTINY -> [DEFICIENCY_RAISED, EVC_REQUIRED, COMMITTEE_REVIEW] -> ...
        stages_data = [
            ("DRAFT", "Draft Application", 0, UserRole.INSTITUTION, 0, False, ["SUBMITTED"]),
            ("SUBMITTED", "Submitted - Pending Scrutiny Assignment", 1, UserRole.SCRUTINY_OFFICER, 2, False, ["UNDER_SCRUTINY"]),
            ("UNDER_SCRUTINY", "Under Scrutiny Review", 2, UserRole.SCRUTINY_OFFICER, 7, False, ["DEFICIENCY_RAISED", "EVC_REQUIRED", "COMMITTEE_REVIEW"]),
            ("DEFICIENCY_RAISED", "Deficiencies Raised - Awaiting College Response", 3, UserRole.INSTITUTION, 7, False, ["RESUBMITTED"]),
            ("RESUBMITTED", "Corrections Resubmitted", 4, UserRole.SCRUTINY_OFFICER, 3, False, ["UNDER_SCRUTINY"]),
            ("EVC_REQUIRED", "EVC Inspection Required - Awaiting Scheduling", 5, UserRole.EVC_COORDINATOR, 5, True, ["EVC_SCHEDULED"]),
            ("EVC_SCHEDULED", "EVC Inspection Scheduled", 6, UserRole.EVC_COORDINATOR, 10, True, ["EVC_COMPLETED"]),
            ("EVC_COMPLETED", "EVC Inspection Completed", 7, UserRole.EVC_COORDINATOR, 3, False, ["COMMITTEE_REVIEW"]),
            ("COMMITTEE_REVIEW", "SAC/SHC Committee Review", 8, UserRole.COMMITTEE_MEMBER, 7, False, ["DECISION_PENDING"]),
            ("DECISION_PENDING", "Final Decision Pending", 9, UserRole.AUTHORISED_OFFICIAL, 5, False, ["APPROVED", "APPROVED_WITH_CONDITIONS", "REJECTED"]),
            ("APPROVED", "Approved", 10, UserRole.AUTHORISED_OFFICIAL, 0, False, ["CLOSED"]),
            ("APPROVED_WITH_CONDITIONS", "Approved with Undertaking Conditions", 11, UserRole.AUTHORISED_OFFICIAL, 30, False, ["CLOSED"]),
            ("REJECTED", "Application Rejected", 12, UserRole.AUTHORISED_OFFICIAL, 0, False, ["CLOSED"]),
            ("CLOSED", "Process Concluded", 13, "SYSTEM", 0, False, [])
        ]

        for key, name, order, role, sla, evc, allowed in stages_data:
            stage = WorkflowStage(
                template_id=template.id,
                stage_key=key,
                name=name,
                order_no=order,
                owner_role=role,
                sla_days=sla,
                requires_evc=evc,
                allowed_next=allowed
            )
            db.add(stage)
        db.commit()
        return template

    @staticmethod
    def get_stage_config(db: Session, template_id: str, stage_key: str) -> Optional[WorkflowStage]:
        return db.query(WorkflowStage).filter(
            WorkflowStage.template_id == template_id,
            WorkflowStage.stage_key == stage_key
        ).first()

    @staticmethod
    def assign_owner(db: Session, role: str, region: Optional[str] = None) -> Optional[User]:
        """
        Rule 2B.2: Automatic assignment by region, then lowest open task workload.
        """
        query = db.query(User).filter(User.role == role, User.is_active == True)
        if region and region.upper() not in ["ALL", "ALL REGIONS"]:
            regional_users = query.filter(User.region == region).all()
            if regional_users:
                candidates = regional_users
            else:
                candidates = query.all() if role not in [UserRole.SCRUTINY_OFFICER, UserRole.EVC_COORDINATOR, UserRole.COMMITTEE_MEMBER] else []
        else:
            candidates = query.all()

        if not candidates:
            return None

        # Count open tasks for each candidate
        candidate_ids = [c.id for c in candidates]
        task_counts = dict(
            db.query(Task.assigned_to, func.count(Task.id))
            .filter(Task.assigned_to.in_(candidate_ids), Task.status.in_(["OPEN", "OVERDUE", "ESCALATED"]))
            .group_by(Task.assigned_to)
            .all()
        )

        # Sort candidates by least open tasks
        candidates.sort(key=lambda u: task_counts.get(u.id, 0))
        return candidates[0]

    @classmethod
    def transition(
        cls,
        db: Session,
        application: Application,
        to_stage_key: str,
        actor: User,
        outcome: Optional[str] = None,
        force_owner_id: Optional[str] = None
    ) -> Application:
        """
        Rule 2B.1 & 2B.4: Template-driven, atomic state transition, logging audit & history.
        """
        # Fetch current stage config
        from_stage_key = application.current_stage_key or application.status
        current_stage = cls.get_stage_config(db, application.template_id, from_stage_key)
        
        target_stage = cls.get_stage_config(db, application.template_id, to_stage_key)
        if not target_stage:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_STAGE", "message": f"Stage '{to_stage_key}' does not exist in template"}
            )

        # Check allowed transitions if from_stage is configured
        if current_stage and current_stage.allowed_next:
            if to_stage_key not in current_stage.allowed_next and actor.role != UserRole.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "INVALID_TRANSITION",
                        "message": f"Transition from '{from_stage_key}' to '{to_stage_key}' is not permitted by template",
                        "allowed": current_stage.allowed_next
                    }
                )

        now = utcnow()
        before_state = {
            "status": application.status,
            "current_stage_key": application.current_stage_key,
            "current_owner_id": application.current_owner_id
        }

        # Close existing open history record for the application
        open_history = db.query(ApplicationStageHistory).filter(
            ApplicationStageHistory.application_id == application.id,
            ApplicationStageHistory.completed_at.is_(None)
        ).first()
        if open_history:
            open_history.completed_at = now
            open_history.outcome = outcome or f"Moved to {to_stage_key}"

        # Complete previous open tasks
        db.query(Task).filter(
            Task.application_id == application.id,
            Task.status.in_(["OPEN", "OVERDUE", "ESCALATED"])
        ).update({"status": "DONE"}, synchronize_session=False)

        # Determine new owner
        new_owner_id = force_owner_id
        if not new_owner_id and target_stage.owner_role not in ["SYSTEM", UserRole.INSTITUTION]:
            # Fetch institution region for regional assignment
            institution = db.query(Institution).filter(Institution.id == application.institution_id).first()
            region = institution.region if institution else None
            assigned_user = cls.assign_owner(db, target_stage.owner_role, region=region)
            if assigned_user:
                new_owner_id = assigned_user.id

        # Compute SLA deadline
        due_at = now + timedelta(days=target_stage.sla_days) if target_stage.sla_days > 0 else None

        # Update application state
        application.status = to_stage_key
        application.current_stage_key = to_stage_key
        application.current_owner_id = new_owner_id

        # Create history record
        history = ApplicationStageHistory(
            application_id=application.id,
            stage_key=to_stage_key,
            entered_at=now,
            due_at=due_at,
            owner_id=new_owner_id,
            actor_id=actor.id if actor else None
        )
        db.add(history)

        # Create new task if owner_role requires action
        if target_stage.owner_role not in ["SYSTEM"] and to_stage_key not in ["CLOSED", "REJECTED"]:
            task = Task(
                application_id=application.id,
                type=target_stage.stage_key,
                assigned_to=new_owner_id,
                role=target_stage.owner_role,
                due_at=due_at or (now + timedelta(days=7)),
                status="OPEN",
                escalation_level=0
            )
            db.add(task)

        after_state = {
            "status": application.status,
            "current_stage_key": application.current_stage_key,
            "current_owner_id": application.current_owner_id
        }

        db.commit()
        db.refresh(application)

        # Tamper-resistant audit log
        log_audit(
            db=db,
            action="STAGE_TRANSITION",
            entity_type="APPLICATION",
            entity_id=application.id,
            actor_id=actor.id,
            before_state=before_state,
            after_state=after_state
        )

        return application
