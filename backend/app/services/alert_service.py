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

        # Read dynamic rules from escalation_rules table
        esc_rules = db.query(EscalationRule).filter(EscalationRule.active == True).all()
        ladder = {}
        for r in esc_rules:
            if r.target_type not in ladder:
                ladder[r.target_type] = {}
            ladder[r.target_type][r.level] = r

        # Dynamic rules for TASK
        t_l1 = ladder.get("TASK", {}).get(1)
        t_l2 = ladder.get("TASK", {}).get(2)
        task_l1_days = t_l1.after_overdue_days if t_l1 else 2
        task_l1_role = t_l1.escalate_to_role if t_l1 else UserRole.AUTHORISED_OFFICIAL
        task_l2_days = t_l2.after_overdue_days if t_l2 else 5
        task_l2_role = t_l2.escalate_to_role if t_l2 else UserRole.AUTHORISED_OFFICIAL

        # Dynamic rules for UNDERTAKING
        u_l1 = ladder.get("UNDERTAKING", {}).get(1)
        u_l2 = ladder.get("UNDERTAKING", {}).get(2)
        und_l1_days = u_l1.after_overdue_days if u_l1 else 2
        und_l1_role = u_l1.escalate_to_role if u_l1 else UserRole.AUTHORISED_OFFICIAL
        und_l2_days = u_l2.after_overdue_days if u_l2 else 5
        und_l2_role = u_l2.escalate_to_role if u_l2 else UserRole.AUTHORISED_OFFICIAL

        # Dynamic rules for DOCUMENT
        d_l1 = ladder.get("DOCUMENT", {}).get(1)
        d_l2 = ladder.get("DOCUMENT", {}).get(2)
        doc_l1_days = d_l1.after_overdue_days if d_l1 else 2
        doc_l1_role = d_l1.escalate_to_role if d_l1 else UserRole.AUTHORISED_OFFICIAL
        doc_l2_days = d_l2.after_overdue_days if d_l2 else 5
        doc_l2_role = d_l2.escalate_to_role if d_l2 else UserRole.AUTHORISED_OFFICIAL

        # 1. Check Task Deadlines and Escalations
        open_tasks = db.query(Task).filter(Task.status.in_(["OPEN", "OVERDUE", "ESCALATED"])).all()
        for task in open_tasks:
            # Overdue check
            if task.due_at and task.due_at < now:
                if task.status == "OPEN":
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

            # Escalation check (stop when resolved)
            days_overdue = (now - task.due_at).days if task.due_at and task.due_at < now else 0
            if days_overdue >= task_l2_days and task.escalation_level < 2:
                task.status = "ESCALATED"
                task.escalation_level = 2
                stats["tasks_escalated"] += 1
                target_user = db.query(User).filter(User.role == task_l2_role).first()
                if target_user:
                    AlertService.send_notification(
                        db,
                        user_id=target_user.id,
                        n_type="ESCALATED",
                        subject=f"ESCALATION LEVEL 2: Application Task {task.id}",
                        body=f"Task {task.type} has been overdue by {days_overdue} days and is escalated to {task_l2_role}.",
                        related_type="TASK",
                        related_id=task.id,
                        dedupe_key=f"ESCALATION_L2:{task.id}"
                    )
            elif days_overdue >= task_l1_days and task.escalation_level < 1:
                task.status = "ESCALATED"
                task.escalation_level = 1
                stats["tasks_escalated"] += 1
                target_user = db.query(User).filter(User.role == task_l1_role).first()
                if target_user:
                    AlertService.send_notification(
                        db,
                        user_id=target_user.id,
                        n_type="ESCALATED",
                        subject=f"ESCALATION LEVEL 1: Application Task {task.id}",
                        body=f"Task {task.type} is overdue by {days_overdue} days and is escalated to {task_l1_role}.",
                        related_type="TASK",
                        related_id=task.id,
                        dedupe_key=f"ESCALATION_L1:{task.id}"
                    )

        # 2. Check Undertaking Deadlines and Escalations
        pending_unds = db.query(Undertaking).filter(Undertaking.status.in_(["PENDING", "OVERDUE", "SUBMITTED"])).all()
        for und in pending_unds:
            if und.due_at and und.due_at < now and und.status not in ["VERIFIED", "COMPLETED"]:
                if und.status not in ["OVERDUE", "SUBMITTED"]:
                    und.status = "OVERDUE"
                    stats["undertakings_overdue"] += 1
                days_overdue = (now - und.due_at).days
                if days_overdue >= und_l2_days:
                    target_user = db.query(User).filter(User.role == und_l2_role).first()
                    if target_user:
                        AlertService.send_notification(
                            db,
                            user_id=target_user.id,
                            n_type="ESCALATED",
                            subject=f"ESCALATION LEVEL 2: Undertaking Overdue - {und.title}",
                            body=f"Undertaking '{und.title}' is overdue by {days_overdue} days and escalated to {und_l2_role}.",
                            related_type="UNDERTAKING",
                            related_id=und.id,
                            dedupe_key=f"ESCALATION_UND_L2:{und.id}"
                        )
                elif days_overdue >= und_l1_days:
                    target_user = db.query(User).filter(User.role == und_l1_role).first()
                    if target_user:
                        AlertService.send_notification(
                            db,
                            user_id=target_user.id,
                            n_type="ESCALATED",
                            subject=f"ESCALATION LEVEL 1: Undertaking Overdue - {und.title}",
                            body=f"Undertaking '{und.title}' is overdue by {days_overdue} days and escalated to {und_l1_role}.",
                            related_type="UNDERTAKING",
                            related_id=und.id,
                            dedupe_key=f"ESCALATION_UND_L1:{und.id}"
                        )

        # 3. Check Document Expiry and Escalations
        docs = db.query(Document).filter(
            Document.valid_until.is_not(None),
            Document.status.in_(["VALID", "EXPIRING", "EXPIRED"])
        ).all()
        for doc in docs:
            days_left = (doc.valid_until - now).days
            if days_left <= 0:
                doc.status = "EXPIRED"
                stats["documents_expiring"] += 1
                days_expired = abs(days_left)
                if days_expired >= doc_l2_days:
                    target_user = db.query(User).filter(User.role == doc_l2_role).first()
                    if target_user:
                        AlertService.send_notification(
                            db,
                            user_id=target_user.id,
                            n_type="ESCALATED",
                            subject=f"ESCALATION LEVEL 2: Expired Compliance Document - {doc.doc_type}",
                            body=f"Compliance document '{doc.doc_type}' ({doc.file_name}) has been expired for {days_expired} days. Escalated to {doc_l2_role}.",
                            related_type="DOCUMENT",
                            related_id=doc.id,
                            dedupe_key=f"ESCALATION_DOC_L2:{doc.id}"
                        )
                elif days_expired >= doc_l1_days:
                    target_user = db.query(User).filter(User.role == doc_l1_role).first()
                    if target_user:
                        AlertService.send_notification(
                            db,
                            user_id=target_user.id,
                            n_type="ESCALATED",
                            subject=f"ESCALATION LEVEL 1: Expired Compliance Document - {doc.doc_type}",
                            body=f"Compliance document '{doc.doc_type}' ({doc.file_name}) has been expired for {days_expired} days. Escalated to {doc_l1_role}.",
                            related_type="DOCUMENT",
                            related_id=doc.id,
                            dedupe_key=f"ESCALATION_DOC_L1:{doc.id}"
                        )
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
