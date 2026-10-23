from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from app.core.database import BaseModel

class Undertaking(BaseModel):
    __tablename__ = "undertakings"
    
    application_id = Column(String(36), ForeignKey("applications.id"), nullable=False, index=True)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    due_at = Column(DateTime, nullable=False, index=True)
    status = Column(String(50), default="PENDING", nullable=False, index=True) # PENDING, SUBMITTED, VERIFIED, REJECTED, OVERDUE
    evidence_document_id = Column(String(36), nullable=True)
    evidence_notes = Column(Text, nullable=True)
    verified_by = Column(String(36), nullable=True)
    verified_at = Column(DateTime, nullable=True)

class Document(BaseModel):
    __tablename__ = "documents"
    
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False, index=True)
    application_id = Column(String(36), ForeignKey("applications.id"), nullable=True, index=True)
    undertaking_id = Column(String(36), ForeignKey("undertakings.id"), nullable=True, index=True)
    doc_type = Column(String(100), nullable=False, index=True) # e.g. LAND_LEASE, FIRE_SAFETY, AFFILIATION_DOC, EVC_REPORT, UNDERTAKING_EVIDENCE
    file_name = Column(String(255), nullable=False)
    storage_key = Column(String(255), nullable=False)
    mime = Column(String(100), nullable=False)
    size = Column(Integer, nullable=False)
    uploaded_by = Column(String(36), nullable=False)
    version_no = Column(Integer, default=1, nullable=False)
    valid_from = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True, index=True)
    status = Column(String(50), default="VALID", nullable=False, index=True) # VALID, EXPIRING, EXPIRED, RENEWED
    replaced_by_id = Column(String(36), nullable=True)
