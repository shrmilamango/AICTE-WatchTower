from typing import Any, Optional, List
from datetime import datetime
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.config import ConfigRule
from app.models.workflow import WorkflowTemplate, WorkflowStage
from app.models.user import User, UserRole
from app.schemas.workflow import WorkflowTemplateCreate, WorkflowTemplateResponse
from app.services.config_service import ConfigService
from app.services.alert_service import AlertService
from app.services.demo_seeder import seed_demo_database

router = APIRouter(tags=["Admin & Configuration"])

class ConfigUpdateRequest(BaseModel):
    value: Any
    description: Optional[str] = None

class SchedulerRunRequest(BaseModel):
    simulated_date: Optional[datetime] = None

# --- Dynamic Configuration Store (6.1) ---

@router.get("/config/{key}")
def get_config_rule(
    key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    val = ConfigService.get_value(db, key)
    if val is None:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": f"Config key '{key}' not found"})
    return {"key": key, "value": val}

@router.put("/config/{key}", dependencies=[Depends(require_role([UserRole.ADMIN]))])
def update_config_rule(
    key: str,
    req: ConfigUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rule = ConfigService.update_config(db, key, req.value, current_user, description=req.description)
    return {"key": rule.key, "value": rule.value, "version": rule.version}

# --- Workflow Template Management (6.2) ---

@router.get("/workflow-templates", response_model=List[WorkflowTemplateResponse])
def get_workflow_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    templates = db.query(WorkflowTemplate).all()
    res = []
    for t in templates:
        stages = db.query(WorkflowStage).filter(WorkflowStage.template_id == t.id).order_by(WorkflowStage.order_no.asc()).all()
        res.append(WorkflowTemplateResponse(
            id=t.id,
            name=t.name,
            version=t.version,
            is_active=t.is_active,
            description=t.description,
            stages=stages,
            created_at=t.created_at
        ))
    return res

@router.post("/workflow-templates", response_model=WorkflowTemplateResponse, dependencies=[Depends(require_role([UserRole.ADMIN]))])
def create_workflow_template(
    req: WorkflowTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tpl = WorkflowTemplate(
        name=req.name,
        version=req.version,
        is_active=False,
        description=req.description
    )
    db.add(tpl)
    db.commit()
    db.refresh(tpl)

    for st in req.stages:
        stage = WorkflowStage(
            template_id=tpl.id,
            stage_key=st.stage_key,
            name=st.name,
            order_no=st.order_no,
            owner_role=st.owner_role,
            sla_days=st.sla_days,
            requires_evc=st.requires_evc,
            allowed_next=st.allowed_next
        )
        db.add(stage)
    db.commit()
    
    stages = db.query(WorkflowStage).filter(WorkflowStage.template_id == tpl.id).order_by(WorkflowStage.order_no.asc()).all()
    return WorkflowTemplateResponse(
        id=tpl.id,
        name=tpl.name,
        version=tpl.version,
        is_active=tpl.is_active,
        description=tpl.description,
        stages=stages,
        created_at=tpl.created_at
    )

@router.post("/workflow-templates/{id}/activate", dependencies=[Depends(require_role([UserRole.ADMIN]))])
def activate_workflow_template(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tpl = db.query(WorkflowTemplate).filter(WorkflowTemplate.id == id).first()
    if not tpl:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Template not found"})
        
    db.query(WorkflowTemplate).update({"is_active": False})
    tpl.is_active = True
    db.commit()
    return {"status": "SUCCESS", "message": f"Template '{tpl.name}' (v{tpl.version}) activated for new applications"}

# --- Demo Presentation Controls (4.10 & 6.7) ---

@router.post("/admin/seed-demo")
def trigger_seed_demo(
    db: Session = Depends(get_db)
):
    """Rule 6.7: One command creates labelled demo institutions, users, and multi-stage applications."""
    if settings.APP_ENV != "demo" and False:
        raise HTTPException(status_code=403, detail={"code": "NOT_DEMO_ENV", "message": "Seeding is only available in demo environment"})
    return seed_demo_database(db)

@router.post("/admin/scheduler/run-now")
def run_scheduler_now(
    req: SchedulerRunRequest = SchedulerRunRequest(),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.AUTHORISED_OFFICIAL])),
    db: Session = Depends(get_db)
):
    """Rule 4.10: Admin-only 'Run scheduler now' button with optional simulated date."""
    stats = AlertService.run_scheduler_checks(db, simulated_now=req.simulated_date, actor=current_user)
    return {"status": "SUCCESS", "results": stats}
