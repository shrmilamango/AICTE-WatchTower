from sqlalchemy import Column, String, Integer, JSON, Text
from app.core.database import BaseModel

class ConfigRule(BaseModel):
    __tablename__ = "config_rules"
    
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(JSON, nullable=False)
    description = Column(Text, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    updated_by = Column(String(36), nullable=True)
