from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

class NotificationResponse(BaseModel):
    id: str
    user_id: str
    channel: str
    type: str
    subject: str
    body: str
    related_type: Optional[str] = None
    related_id: Optional[str] = None
    status: str
    sent_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ReminderRuleResponse(BaseModel):
    id: str
    target_type: str
    offsets_days: List[int]
    channels: List[str]
    active: bool

    class Config:
        from_attributes = True

class ReminderRuleUpdate(BaseModel):
    offsets_days: List[int]
    channels: Optional[List[str]] = None
    active: Optional[bool] = None

class EscalationRuleResponse(BaseModel):
    id: str
    target_type: str
    level: int
    after_overdue_days: int
    escalate_to_role: str
    active: bool

    class Config:
        from_attributes = True

class EscalationRuleUpdate(BaseModel):
    after_overdue_days: int
    escalate_to_role: str
    active: Optional[bool] = None

class EscalationLadderItem(BaseModel):
    target_type: str # TASK, UNDERTAKING, DOCUMENT
    l1_role: str = "AUTHORISED_OFFICIAL"
    l1_days: int = 2
    l2_role: str = "AUTHORISED_OFFICIAL"
    l2_days: int = 5

class EscalationLadderBatchRequest(BaseModel):
    items: List[EscalationLadderItem]

class RiskFactor(BaseModel):
    rule: str
    points: int
    explanation: str

class RiskScoreResponse(BaseModel):
    id: str
    application_id: str
    app_no: Optional[str] = None
    institution_name: Optional[str] = None
    score: int
    level: str # LOW, MEDIUM, HIGH
    factors: List[RiskFactor] = []
    computed_at: datetime

    class Config:
        from_attributes = True

class AuditLogResponse(BaseModel):
    id: str
    actor_id: Optional[str] = None
    actor_name: Optional[str] = None
    action: str
    entity_type: str
    entity_id: str
    before_state: Optional[Any] = None
    after_state: Optional[Any] = None
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class DashboardSummary(BaseModel):
    total_applications: int = 0
    under_scrutiny: int = 0
    evc_awaiting_scheduling: int = 0
    overdue_applications: int = 0
    compliance_pending: int = 0
    documents_expiring_soon: int = 0
    
    # Role-specific metrics
    institution_approved: int = 0
    institution_deficiencies: int = 0
    my_open_tasks: int = 0
    my_overdue_tasks: int = 0
    evc_scheduled: int = 0
    evc_reports_pending: int = 0
    committee_review_count: int = 0
