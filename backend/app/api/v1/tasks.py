from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db, utcnow
from app.core.deps import get_current_user, require_role
from app.models.workflow import Task, Application
from app.models.institution import Institution
from app.models.user import User, UserRole
from app.schemas.workflow import TaskResponse
from app.services.workflow_service import WorkflowService

router = APIRouter(tags=["Tasks & Queues"])

class ReassignRequest(BaseModel):
    assigned_to: str

def enrich_task_response(t: Task, db: Session) -> TaskResponse:
    app = db.query(Application).filter(Application.id == t.application_id).first()
    inst = db.query(Institution).filter(Institution.id == app.institution_id).first() if app else None
    assignee = db.query(User).filter(User.id == t.assigned_to).first() if t.assigned_to else None
    now = utcnow()
    is_overdue = (t.due_at < now) if t.due_at else False

    return TaskResponse(
        id=t.id,
        application_id=t.application_id,
        app_no=app.app_no if app else None,
        institution_name=inst.name if inst else "Unknown",
        programme=app.programme if app else None,
        type=t.type,
        assigned_to=t.assigned_to,
        assigned_to_name=assignee.full_name if assignee else "Unassigned",
        role=t.role,
        due_at=t.due_at,
        status=t.status,
        escalation_level=t.escalation_level,
        created_at=t.created_at,
        is_overdue=is_overdue
    )

@router.get("/tasks/my", response_model=List[TaskResponse])
def get_my_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rule 2C.1: Officer sees only their open tasks, sorted by due date, overdue first."""
    tasks = db.query(Task).filter(
        Task.assigned_to == current_user.id,
        Task.status.in_(["OPEN", "OVERDUE", "ESCALATED"])
    ).order_by(Task.due_at.asc()).all()
    return [enrich_task_response(t, db) for t in tasks]

@router.get("/tasks", response_model=List[TaskResponse])
def get_all_tasks(
    status: Optional[str] = None,
    role: Optional[str] = None,
    assigned_to: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Task)
    if status:
        query = query.filter(Task.status == status)
    if role:
        query = query.filter(Task.role == role)
    if assigned_to:
        query = query.filter(Task.assigned_to == assigned_to)
    tasks = query.order_by(Task.due_at.asc()).all()
    return [enrich_task_response(t, db) for t in tasks]

@router.patch("/tasks/{id}/reassign", response_model=TaskResponse)
def reassign_task(
    id: str,
    req: ReassignRequest,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.AUTHORISED_OFFICIAL])),
    db: Session = Depends(get_db)
):
    t = WorkflowService.reassign_task(db, id, req.assigned_to, current_user)
    return enrich_task_response(t, db)

@router.patch("/cases/{id}/assign", response_model=TaskResponse)
def reassign_case(
    id: str,
    req: ReassignRequest,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.AUTHORISED_OFFICIAL])),
    db: Session = Depends(get_db)
):
    return reassign_task(id, req, current_user, db)
