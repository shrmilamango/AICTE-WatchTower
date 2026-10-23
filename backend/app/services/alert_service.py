from datetime import datetime, timedelta, timezone
from typing import Optional, List
from sqlalchemy.orm import Session
from app.core.database import utcnow
from app.core.audit import log_audit
from app.models.alert import Notification, ReminderRule, EscalationRule
from app.models.workflow import Task, Application
from app.models.compliance import Undertaking, Document
from app.models.user import User, UserRole
from app.models.institution import Institution

class AlertService:
    @staticmethod
    def send_notification(
        db: Session,
        user_id: str,
        n_type: str,
        subject: str,
        body: str,
        related_type: Optional[str] = None,
        related_id: Optional[str] = None,
        dedupe_key: Optional[str] = None,
        channel: str = "IN_APP"
    ) -> Optional[Notification]:
        # Deduplication check
        if dedupe_key:
            existing = db.query(Notification).filter(Notification.dedupe_key == dedupe_key).first()
            if existing:
                return None

        clean_dedupe = dedupe_key or f"{n_type}:{user_id}:{utcnow().strftime('%Y%m%d%H%M%S%f')}"
        notification = Notification(
            user_id=user_id,
            channel=channel,
            type=n_type,
            subject=subject,
            body=body,
            related_type=related_type,
            related_id=related_id,
            dedupe_key=clean_dedupe,
            status="QUEUED",
            sent_at=utcnow()
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)

        # Immediate simulation of dispatch to SENT
        notification.status = "SENT"
        db.commit()
        return notification

    @staticmethod
    def run_scheduler_checks(
        db: Session,
        simulated_now: Optional[datetime] = None,
        actor: Optional[User] = None
    ) -> dict:
        now = simulated_now or utcnow()
        date_str = now.strftime("%Y-%m-%d")
        stats = {
            "tasks_overdue": 0,
            "tasks_escalated": 0,
            "undertakings_overdue": 0,
            "documents_expiring": 0,
            "reminders_dispatched": 0
        }

        # 1. Check Task Deadlines and Reminders
        open_tasks = db.query(Task).filter(Task.status.in_(["OPEN", "OVERDUE"])).all()
        for task in open_tasks:
            # Overdue check
            if task.due_at and task.due_at < now:
                if task.status != "OVERDUE":
                    task.status = "OVERDUE"
                    stats["tasks_overdue"] += 1
                    if task.assigned_to:
                        AlertService.send_notification(
                            db,
                            user_id=task.assigned_to,
                            n_type="TASK_OVERDUE",
                            subject=f"URGENT: Task Overdue for Application",
                            body=f"Your assigned task ({task.type}) was due on {task.due_at.strftime('%Y-%m-%d')} and is now overdue.",
                            related_type="TASK",
                            related_id=task.id,
                            dedupe_key=f"OVERDUE_TASK:{task.id}:{date_str}"
                        )

            # Escalation check
            days_overdue = (now - task.due_at).days if task.due_at and task.due_at < now else 0
            if days_overdue >= 5 and task.escalation_level < 2:
                task.status = "ESCALATED"
                task.escalation_level = 2
                stats["tasks_escalated"] += 1
                admin_user = db.query(User).filter(User.role == UserRole.ADMIN).first()
                if admin_user:
                    AlertService.send_notification(
                        db,
                        user_id=admin_user.id,
                        n_type="ESCALATED",
                        subject=f"ESCALATION LEVEL 2: Application Task {task.id}",
                        body=f"Task {task.type} has been overdue by {days_overdue} days and is escalated to System Administration.",
                        related_type="TASK",
                        related_id=task.id,
                        dedupe_key=f"ESCALATION_L2:{task.id}:{date_str}"
                    )
            elif days_overdue >= 2 and task.escalation_level < 1:
                task.status = "ESCALATED"
                task.escalation_level = 1
                stats["tasks_escalated"] += 1
                official_user = db.query(User).filter(User.role == UserRole.AUTHORISED_OFFICIAL).first()
                if official_user:
                    AlertService.send_notification(
                        db,
                        user_id=official_user.id,
                        n_type="ESCALATED",
                        subject=f"ESCALATION LEVEL 1: Application Task {task.id}",
                        body=f"Task {task.type} is overdue by {days_overdue} days and is escalated to Regional Authorised Official.",
                        related_type="TASK",
                        related_id=task.id,
                        dedupe_key=f"ESCALATION_L1:{task.id}:{date_str}"
                    )

        # 2. Check Undertaking Deadlines
        pending_unds = db.query(Undertaking).filter(Undertaking.status.in_(["PENDING", "SUBMITTED"])).all()
        for und in pending_unds:
            if und.due_at and und.due_at < now and und.status != "VERIFIED":
                und.status = "OVERDUE"
                stats["undertakings_overdue"] += 1
                inst_users = db.query(User).filter(User.institution_id == und.institution_id).all()
                for u in inst_users:
                    AlertService.send_notification(
                        db,
                        user_id=u.id,
                        n_type="UNDERTAKING_OVERDUE",
                        subject=f"COMPLIANCE OVERDUE: {und.title}",
                        body=f"Undertaking condition '{und.title}' was due on {und.due_at.strftime('%Y-%m-%d')} and has lapsed.",
                        related_type="UNDERTAKING",
                        related_id=und.id,
                        dedupe_key=f"UND_OVERDUE:{und.id}:{date_str}"
                    )

        # 3. Check Document Expiry
        docs = db.query(Document).filter(
            Document.valid_until.is_not(None),
            Document.status.in_(["VALID", "EXPIRING"])
        ).all()
        for doc in docs:
            days_left = (doc.valid_until - now).days
            if days_left <= 0:
                doc.status = "EXPIRED"
                stats["documents_expiring"] += 1
            elif days_left <= 30:
                doc.status = "EXPIRING"
                stats["documents_expiring"] += 1
                inst_users = db.query(User).filter(User.institution_id == doc.institution_id).all()
                for u in inst_users:
                    AlertService.send_notification(
                        db,
                        user_id=u.id,
                        n_type="DOCUMENT_EXPIRING",
                        subject=f"DOCUMENT EXPIRY WARNING: {doc.doc_type}",
                        body=f"Your {doc.doc_type} ({doc.file_name}) will expire in {days_left} days. Please upload a renewed document.",
                        related_type="DOCUMENT",
                        related_id=doc.id,
                        dedupe_key=f"DOC_EXPIRY:{doc.id}:{days_left}:{date_str}"
                    )

        db.commit()

        if actor:
            log_audit(
                db=db,
                action="RUN_SCHEDULER_NOW",
                entity_type="SYSTEM",
                entity_id="SCHEDULER",
                actor_id=actor.id,
                after_state=stats
            )
        return stats
