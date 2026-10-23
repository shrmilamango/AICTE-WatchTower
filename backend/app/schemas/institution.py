from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class InstitutionBase(BaseModel):
    name: str
    aicte_code: str
    region: str
    state: str
    address: str
    contact_name: str
    contact_email: EmailStr
    contact_phone: str
    status: str = "ACTIVE"

class InstitutionCreate(InstitutionBase):
    pass

class InstitutionUpdate(BaseModel):
    name: Optional[str] = None
    region: Optional[str] = None
    state: Optional[str] = None
    address: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    status: Optional[str] = None

class InstitutionResponse(InstitutionBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class InstitutionSummary(BaseModel):
    institution: InstitutionResponse
    total_applications: int
    open_deficiencies: int
    pending_undertakings: int
    expiring_documents: int
