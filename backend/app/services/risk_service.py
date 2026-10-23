from datetime import datetime, timezone
from typing import List, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import utcnow
from app.models.workflow import Application, ApplicationStageHistory, Task, WorkflowStage
from app.models.scrutiny import ScrutinyReview
from app.models.evc import EvcVisit
from app.models.compliance import Undertaking, Document
from app.models.risk import RiskScore

WORKLOAD_THRESHOLD = 5

class RiskService:
    @staticmethod
    def compute_risk(db: Session, application: Application) -> RiskScore:
        score = 0
        factors = []
        now = utcnow()

        # Rule 1: More than 70% of the stage SLA used and stage not complete (+20)
        current_history = db.query(ApplicationStageHistory).filter(
            ApplicationStageHistory.application_id == application.id,
            ApplicationStageHistory.completed_at.is_(None)
        ).first()

        if current_history and current_history.due_at:
            total_duration = (current_history.due_at - current_history.entered_at).total_seconds()
            if total_duration > 0:
                elapsed = (now - current_history.entered_at).total_seconds()
                ratio = elapsed / total_duration
                if ratio >= 0.7:
                    score += 20
                    pct = int(ratio * 100)
                    factors.append({
                        "rule": "SLA_CONSUMPTION_HIGH",
                        "points": 20,
                        "explanation": f"More than 70% of the stage SLA consumed ({pct}% of allotted time used)."
                    })

        # Rule 2: Task already overdue (+35)
        overdue_task = db.query(Task).filter(
            Task.application_id == application.id,
            Task.status.in_(["OVERDUE", "ESCALATED"])
        ).first()
        if overdue_task:
            score += 35
            factors.append({
                "rule": "TASK_OVERDUE",
                "points": 35,
                "explanation": f"Active task '{overdue_task.type}' is currently overdue (due: {overdue_task.due_at.strftime('%Y-%m-%d')})."
            })

        # Rule 3: Two or more deficiency rounds (+15)
        deficiency_rounds = db.query(ScrutinyReview).filter(
            ScrutinyReview.application_id == application.id,
            ScrutinyReview.outcome == "DEFICIENT"
        ).count()
        if deficiency_rounds >= 2:
            score += 15
            factors.append({
                "rule": "MULTIPLE_DEFICIENCY_ROUNDS",
                "points": 15,
                "explanation": f"Application has undergone {deficiency_rounds} rounds of deficiencies."
            })

        # Rule 4: EVC required but not scheduled after its target date (+20)
        evc = db.query(EvcVisit).filter(
            EvcVisit.application_id == application.id,
            EvcVisit.status == "REQUIRED"
        ).first()
        if evc and evc.target_date and evc.target_date < now:
            score += 20
            factors.append({
                "rule": "EVC_UNSCHEDULED_PAST_TARGET",
                "points": 20,
                "explanation": f"EVC visit was required by target date {evc.target_date.strftime('%Y-%m-%d')} but remains unscheduled."
            })

        # Rule 5: Undertaking due within 7 days and not submitted (+15)
        pending_und = db.query(Undertaking).filter(
            Undertaking.application_id == application.id,
            Undertaking.status.in_(["PENDING", "OVERDUE"])
        ).all()
        for u in pending_und:
            if u.due_at and (u.due_at - now).days <= 7:
                score += 15
                factors.append({
                    "rule": "UNDERTAKING_DUE_SOON",
                    "points": 15,
                    "explanation": f"Undertaking '{u.title}' is due in {(u.due_at - now).days} days and evidence is not submitted."
                })
                break

        # Rule 6: Key document expired or expiring within 30 days (+10)
        exp_doc = db.query(Document).filter(
            Document.application_id == application.id,
            Document.status.in_(["EXPIRING", "EXPIRED"])
        ).first()
        if exp_doc:
            score += 10
            factors.append({
                "rule": "DOCUMENT_EXPIRING",
                "points": 10,
                "explanation": f"Required compliance document '{exp_doc.doc_type}' ({exp_doc.file_name}) is {exp_doc.status.lower()}."
            })

        # Rule 7: Officer's open tasks above workload threshold (+10)
        if application.current_owner_id:
            officer_tasks_count = db.query(Task).filter(
                Task.assigned_to == application.current_owner_id,
                Task.status.in_(["OPEN", "OVERDUE", "ESCALATED"])
            ).count()
            if officer_tasks_count > WORKLOAD_THRESHOLD:
                score += 10
                factors.append({
                    "rule": "OFFICER_OVERLOADED",
                    "points": 10,
                    "explanation": f"Assigned officer's workload ({officer_tasks_count} active cases) exceeds threshold of {WORKLOAD_THRESHOLD}."
                })

        # Cap score at 100
        score = min(score, 100)

        # Categorize level
        if score >= 60:
            level = "HIGH"
        elif score >= 30:
            level = "MEDIUM"
        else:
            level = "LOW"

        # Update or create RiskScore in DB
        risk_record = db.query(RiskScore).filter(RiskScore.application_id == application.id).first()
        if not risk_record:
            risk_record = RiskScore(application_id=application.id)
            db.add(risk_record)

        risk_record.score = score
        risk_record.level = level
        risk_record.factors = factors
        risk_record.computed_at = now
        db.commit()
        db.refresh(risk_record)

        return risk_record

    @staticmethod
    def recompute_all(db: Session) -> int:
        open_apps = db.query(Application).filter(
            Application.status.notin_(["DRAFT", "CLOSED", "REJECTED"])
        ).all()
        count = 0
        for app in open_apps:
            RiskService.compute_risk(db, app)
            count += 1
        return count
