from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UndertakingCreate(BaseModel):
    title: str
    description: str
    due_days: int = 30

class UndertakingEvidenceSubmit(BaseModel):
    evidence_document_id: Optional[str] = None
    evidence_notes: str

class UndertakingVerify(BaseModel):
    status: str # VERIFIED or REJECTED
    remarks: Optional[str] = None
    new_due_days: Optional[int] = None # if rejected

class UndertakingResponse(BaseModel):
    id: str
    application_id: str
    app_no: Optional[str] = None
    institution_id: str
    institution_name: Optional[str] = None
    title: str
    description: str
    due_at: datetime
    status: str
    evidence_document_id: Optional[str] = None
    evidence_notes: Optional[str] = None
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_at: datetime
    is_overdue: bool = False

    class Config:
        from_attributes = True

class DocumentResponse(BaseModel):
    id: str
    institution_id: str
    application_id: Optional[str] = None
    undertaking_id: Optional[str] = None
    doc_type: str
    file_name: str
    storage_key: str
    mime: str
    size: int
    uploaded_by: str
    version_no: int
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    status: str
    replaced_by_id: Optional[str] = None
    created_at: datetime
    days_until_expiry: Optional[int] = None

    class Config:
        from_attributes = True

class DocumentRenewRequest(BaseModel):
    valid_from: datetime
    valid_until: datetime
