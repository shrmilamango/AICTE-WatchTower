from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime

class StageConfig(BaseModel):
    stage_key: str
    name: str
    order_no: int
    owner_role: str
    sla_days: int = 7
    requires_evc: bool = False
    allowed_next: list[str] = []

class WorkflowTemplateCreate(BaseModel):
    name: str
    version: int = 1
    description: Optional[str] = None
    stages: list[StageConfig] = []

class WorkflowStageResponse(BaseModel):
    id: str
    stage_key: str
    name: str
    order_no: int
    owner_role: str
    sla_days: int
    requires_evc: bool
    allowed_next: list[str]

    class Config:
        from_attributes = True

class WorkflowTemplateResponse(BaseModel):
    id: str
    name: str
    version: int
    is_active: bool
    description: Optional[str] = None
    stages: list[WorkflowStageResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True

class ApplicationCreate(BaseModel):
    programme: str
    academic_year: str = "2026-27"
    form_data: dict[str, Any] = {}

class ApplicationUpdate(BaseModel):
    programme: Optional[str] = None
    academic_year: Optional[str] = None
    form_data: Optional[dict[str, Any]] = None

class ApplicationResponse(BaseModel):
    id: str
    app_no: str
    institution_id: str
    template_id: str
    programme: str
    academic_year: str
    form_data: dict[str, Any]
    status: str
    current_stage_key: Optional[str] = None
    current_owner_id: Optional[str] = None
    submitted_at: Optional[datetime] = None
    decided_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    # Enriched fields for UX
    institution_name: Optional[str] = None
    owner_name: Optional[str] = None
    pending_with: Optional[str] = None
    days_pending: Optional[int] = None
    risk_level: Optional[str] = "LOW"
    risk_score: Optional[int] = 0

    class Config:
        from_attributes = True

class ApplicationStageHistoryResponse(BaseModel):
    id: str
    application_id: str
    stage_key: str
    entered_at: datetime
    due_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    owner_id: Optional[str] = None
    owner_name: Optional[str] = None
    outcome: Optional[str] = None

    class Config:
        from_attributes = True

class TaskResponse(BaseModel):
    id: str
    application_id: str
    app_no: Optional[str] = None
    institution_name: Optional[str] = None
    programme: Optional[str] = None
    type: str
    assigned_to: Optional[str] = None
    assigned_to_name: Optional[str] = None
    role: str
    due_at: datetime
    status: str
    escalation_level: int
    created_at: datetime
    is_overdue: bool = False

    class Config:
        from_attributes = True

class TimelineItem(BaseModel):
    id: str
    type: str # STAGE, SCRUTINY, DEFICIENCY, EVC, COMMITTEE, DECISION, ESCALATION
    title: str
    description: str
    actor_name: Optional[str] = None
    actor_role: Optional[str] = None
    timestamp: datetime
    metadata: dict[str, Any] = {}
