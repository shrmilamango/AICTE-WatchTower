from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey
from app.core.database import BaseModel, utcnow

class RiskScore(BaseModel):
    __tablename__ = "risk_scores"
    
    application_id = Column(String(36), ForeignKey("applications.id"), unique=True, nullable=False, index=True)
    score = Column(Integer, default=0, nullable=False) # 0 to 100
    level = Column(String(20), default="LOW", nullable=False) # LOW, MEDIUM, HIGH
    factors = Column(JSON, default=list, nullable=False) # list of {rule: str, points: int, explanation: str}
    computed_at = Column(DateTime, default=utcnow, nullable=False)
