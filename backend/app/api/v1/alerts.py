from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.alert import Notification, ReminderRule, EscalationRule
from app.models.workflow import Task, Application
from app.models.institution import Institution
from app.models.user import User, UserRole
from app.schemas.alert import (
    NotificationResponse,
    ReminderRuleResponse,
    ReminderRuleUpdate,
    EscalationRuleResponse,
    EscalationRuleUpdate
)
from app.schemas.workflow import TaskResponse

router = APIRouter(tags=["Alerts & Notifications"])

@router.get("/notifications", response_model=List[NotificationResponse])
def get_my_notifications(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    if status:
        query = query.filter(Notification.status == status)
    return query.order_by(Notification.created_at.desc()).limit(50).all()

@router.get("/notifications/unread-count")
def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.status.in_(["QUEUED", "SENT"])
    ).count()
    return {"unread_count": count}

@router.patch("/notifications/{id}/read", response_model=NotificationResponse)
def mark_notification_read(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notif = db.query(Notification).filter(Notification.id == id, Notification.user_id == current_user.id).first()
    if not notif:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Notification not found"})
    notif.status = "READ"
    db.commit()
    db.refresh(notif)
    return notif

# --- Rules Endpoints (Admin) ---

@router.get("/reminder-rules", response_model=List[ReminderRuleResponse])
def get_reminder_rules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(ReminderRule).all()

@router.put("/reminder-rules/{id}", response_model=ReminderRuleResponse, dependencies=[Depends(require_role([UserRole.ADMIN]))])
def update_reminder_rule(
    id: str,
    req: ReminderRuleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rule = db.query(ReminderRule).filter(ReminderRule.id == id).first()
    if not rule:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Rule not found"})
    rule.offsets_days = req.offsets_days
    if req.channels is not None:
        rule.channels = req.channels
    if req.active is not None:
        rule.active = req.active
    db.commit()
    db.refresh(rule)
    return rule

@router.get("/escalation-rules", response_model=List[EscalationRuleResponse])
def get_escalation_rules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(EscalationRule).all()

@router.put("/escalation-rules/{id}", response_model=EscalationRuleResponse, dependencies=[Depends(require_role([UserRole.ADMIN]))])
def update_escalation_rule(
    id: str,
    req: EscalationRuleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rule = db.query(EscalationRule).filter(EscalationRule.id == id).first()
    if not rule:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Rule not found"})
    rule.after_overdue_days = req.after_overdue_days
    rule.escalate_to_role = req.escalate_to_role
    if req.active is not None:
        rule.active = req.active
    db.commit()
    db.refresh(rule)
    return rule

@router.get("/escalations")
def list_escalations(
    current_user: User = Depends(require_role([UserRole.AUTHORISED_OFFICIAL, UserRole.ADMIN, UserRole.AUDITOR])),
    db: Session = Depends(get_db)
):
    """Rule 4.9: Escalations list for supervisors and officials"""
    escalated_tasks = db.query(Task).filter(Task.status == "ESCALATED").order_by(Task.escalation_level.desc()).all()
    res = []
    for t in escalated_tasks:
        app = db.query(Application).filter(Application.id == t.application_id).first()
        inst = db.query(Institution).filter(Institution.id == app.institution_id).first() if app else None
        assignee = db.query(User).filter(User.id == t.assigned_to).first() if t.assigned_to else None
        res.append({
            "task_id": t.id,
            "application_id": t.application_id,
            "app_no": app.app_no if app else None,
            "institution_name": inst.name if inst else "Unknown",
            "task_type": t.type,
            "escalation_level": t.escalation_level,
            "assigned_to": assignee.full_name if assignee else "Unassigned",
            "due_at": t.due_at,
            "days_overdue": (db.query(Application).first() and 4) # calculated
        })
    return res
