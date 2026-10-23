from sqlalchemy import Column, String, DateTime, JSON, Text, ForeignKey
from app.core.database import BaseModel

class EvcVisit(BaseModel):
    __tablename__ = "evc_visits"
    
    application_id = Column(String(36), ForeignKey("applications.id"), nullable=False, index=True)
    status = Column(String(50), default="REQUIRED", nullable=False, index=True) # REQUIRED, SCHEDULED, COMPLETED, CANCELLED
    target_date = Column(DateTime, nullable=True)
    scheduled_date = Column(DateTime, nullable=True)
    members = Column(JSON, default=list, nullable=False) # list of expert names, affiliations
    coordinator_id = Column(String(36), nullable=True)
    report_document_id = Column(String(36), nullable=True)
    remarks = Column(Text, nullable=True)
