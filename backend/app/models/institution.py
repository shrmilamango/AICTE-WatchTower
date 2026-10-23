from sqlalchemy import Column, String, Text
from app.core.database import BaseModel

class Institution(BaseModel):
    __tablename__ = "institutions"
    
    name = Column(String(255), nullable=False)
    aicte_code = Column(String(50), unique=True, nullable=False, index=True)
    region = Column(String(50), nullable=False, index=True)
    state = Column(String(100), nullable=False)
    address = Column(Text, nullable=False)
    contact_name = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(50), nullable=False)
    status = Column(String(50), default="ACTIVE", nullable=False) # ACTIVE, SUSPENDED, DEMO
