from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON, Text, ForeignKey
from app.core.database import BaseModel

class Notification(BaseModel):
    __tablename__ = "notifications"
    
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    channel = Column(String(50), default="IN_APP", nullable=False) # IN_APP, EMAIL, SMS
    type = Column(String(100), nullable=False) # APPLICATION_SUBMITTED, TASK_ASSIGNED, DEADLINE_APPROACHING, TASK_OVERDUE, ESCALATED, DEFICIENCY_RAISED, RESUBMISSION_RECEIVED, EVC_SCHEDULED, DECISION_RECORDED, UNDERTAKING_OVERDUE, DOCUMENT_EXPIRING
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    related_type = Column(String(50), nullable=True) # APPLICATION, TASK, UNDERTAKING, DOCUMENT
    related_id = Column(String(36), nullable=True)
    dedupe_key = Column(String(255), unique=True, nullable=False, index=True)
    status = Column(String(50), default="QUEUED", nullable=False, index=True) # QUEUED, SENT, FAILED, READ
    sent_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)

class ReminderRule(BaseModel):
    __tablename__ = "reminder_rules"
    
    target_type = Column(String(50), unique=True, nullable=False, index=True) # TASK, UNDERTAKING, DOCUMENT
    offsets_days = Column(JSON, default=list, nullable=False) # e.g. [-30, -7, 0] or [-2, -1, 0]
    channels = Column(JSON, default=lambda: ["IN_APP", "EMAIL"], nullable=False)
    active = Column(Boolean, default=True, nullable=False)

class EscalationRule(BaseModel):
    __tablename__ = "escalation_rules"
    
    target_type = Column(String(50), nullable=False, index=True) # TASK, UNDERTAKING
    level = Column(Integer, nullable=False) # 1, 2
    after_overdue_days = Column(Integer, nullable=False)
    escalate_to_role = Column(String(50), nullable=False) # e.g. AUTHORISED_OFFICIAL, ADMIN
    active = Column(Boolean, default=True, nullable=False)
