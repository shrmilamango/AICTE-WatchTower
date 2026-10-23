from sqlalchemy import Column, String, Boolean, Integer, DateTime
from app.core.database import BaseModel

class UserRole:
    INSTITUTION = "INSTITUTION"
    SCRUTINY_OFFICER = "SCRUTINY_OFFICER"
    EVC_COORDINATOR = "EVC_COORDINATOR"
    COMMITTEE_MEMBER = "COMMITTEE_MEMBER"
    AUTHORISED_OFFICIAL = "AUTHORISED_OFFICIAL"
    ADMIN = "ADMIN"
    AUDITOR = "AUDITOR"
    
    ALL = [
        INSTITUTION,
        SCRUTINY_OFFICER,
        EVC_COORDINATOR,
        COMMITTEE_MEMBER,
        AUTHORISED_OFFICIAL,
        ADMIN,
        AUDITOR
    ]

class User(BaseModel):
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, index=True)
    institution_id = Column(String(36), nullable=True, index=True)
    region = Column(String(50), nullable=True, index=True) # E.g. "NORTH", "SOUTH", "WEST", "EAST"
    is_active = Column(Boolean, default=True, nullable=False)
    failed_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    last_login = Column(DateTime, nullable=True)
