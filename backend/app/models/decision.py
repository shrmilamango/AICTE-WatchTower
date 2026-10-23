from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from app.core.database import BaseModel

class Decision(BaseModel):
    __tablename__ = "decisions"
    
    application_id = Column(String(36), ForeignKey("applications.id"), nullable=False, index=True)
    decision = Column(String(50), nullable=False, index=True) # APPROVE, APPROVED_WITH_CONDITIONS, REJECT
    decided_by = Column(String(36), nullable=False)
    order_ref = Column(String(100), nullable=True)
    remarks = Column(Text, nullable=True)
    decided_at = Column(DateTime, nullable=False)
