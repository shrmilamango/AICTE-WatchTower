from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from app.core.database import BaseModel

class CommitteeReview(BaseModel):
    __tablename__ = "committee_reviews"
    
    application_id = Column(String(36), ForeignKey("applications.id"), nullable=False, index=True)
    committee_type = Column(String(50), nullable=False) # SAC, SHC
    reviewer_id = Column(String(36), nullable=False, index=True)
    status = Column(String(50), default="PENDING", nullable=False) # PENDING, COMPLETED
    recommendation = Column(String(100), nullable=True) # RECOMMENDED, NOT_RECOMMENDED, CONDITIONAL
    remarks = Column(Text, nullable=True)
    due_at = Column(DateTime, nullable=True)
