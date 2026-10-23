from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from app.core.database import BaseModel

class ScrutinyReview(BaseModel):
    __tablename__ = "scrutiny_reviews"
    
    application_id = Column(String(36), ForeignKey("applications.id"), nullable=False, index=True)
    reviewer_id = Column(String(36), nullable=False, index=True)
    round_no = Column(Integer, default=1, nullable=False)
    outcome = Column(String(50), nullable=False) # PASS, DEFICIENT
    remarks = Column(Text, nullable=True)

class Deficiency(BaseModel):
    __tablename__ = "deficiencies"
    
    review_id = Column(String(36), ForeignKey("scrutiny_reviews.id"), nullable=False, index=True)
    item = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(50), default="OPEN", nullable=False, index=True) # OPEN, RESOLVED
    due_at = Column(DateTime, nullable=False)
    response_text = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
