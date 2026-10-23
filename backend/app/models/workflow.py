from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON, Text, ForeignKey
from app.core.database import BaseModel

class WorkflowTemplate(BaseModel):
    __tablename__ = "workflow_templates"
    
    name = Column(String(100), nullable=False)
    version = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    description = Column(Text, nullable=True)

class WorkflowStage(BaseModel):
    __tablename__ = "workflow_stages"
    
    template_id = Column(String(36), ForeignKey("workflow_templates.id"), nullable=False, index=True)
    stage_key = Column(String(50), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    order_no = Column(Integer, nullable=False)
    owner_role = Column(String(50), nullable=False) # e.g. SCRUTINY_OFFICER, EVC_COORDINATOR, etc.
    sla_days = Column(Integer, default=7, nullable=False)
    requires_evc = Column(Boolean, default=False, nullable=False)
    allowed_next = Column(JSON, default=list, nullable=False) # list of stage_keys

class Application(BaseModel):
    __tablename__ = "applications"
    
    app_no = Column(String(50), unique=True, nullable=False, index=True)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False, index=True)
    template_id = Column(String(36), ForeignKey("workflow_templates.id"), nullable=False)
    programme = Column(String(100), nullable=False) # Engineering, Management, Pharmacy, etc.
    academic_year = Column(String(20), nullable=False) # 2026-27
    form_data = Column(JSON, default=dict, nullable=False)
    status = Column(String(50), default="DRAFT", nullable=False, index=True)
    current_stage_key = Column(String(50), nullable=True, index=True)
    current_owner_id = Column(String(36), nullable=True, index=True)
    submitted_at = Column(DateTime, nullable=True)
    decided_at = Column(DateTime, nullable=True)

class ApplicationStageHistory(BaseModel):
    __tablename__ = "application_stage_history"
    
    application_id = Column(String(36), ForeignKey("applications.id"), nullable=False, index=True)
    stage_key = Column(String(50), nullable=False)
    entered_at = Column(DateTime, nullable=False)
    due_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    owner_id = Column(String(36), nullable=True)
    outcome = Column(String(100), nullable=True)

class Task(BaseModel):
    __tablename__ = "tasks"
    
    application_id = Column(String(36), ForeignKey("applications.id"), nullable=False, index=True)
    type = Column(String(50), nullable=False) # SCRUTINY, EVC, COMMITTEE, DECISION, DEFICIENCY
    assigned_to = Column(String(36), nullable=True, index=True)
    role = Column(String(50), nullable=False)
    due_at = Column(DateTime, nullable=False, index=True)
    status = Column(String(50), default="OPEN", nullable=False, index=True) # OPEN, DONE, OVERDUE, ESCALATED
    escalation_level = Column(Integer, default=0, nullable=False)
