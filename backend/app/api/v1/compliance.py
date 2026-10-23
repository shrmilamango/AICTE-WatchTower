from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.database import get_db, utcnow
from app.core.deps import get_current_user, require_role, verify_institution_access
from app.models.compliance import Undertaking, Document
from app.models.workflow import Application
from app.models.institution import Institution
from app.models.user import User, UserRole
from app.schemas.compliance import (
    UndertakingResponse,
    UndertakingEvidenceSubmit,
    UndertakingVerify,
    DocumentResponse,
    DocumentRenewRequest
)
from app.services.compliance_service import ComplianceService

router = APIRouter(tags=["Compliance & Documents"])

def enrich_undertaking(u: Undertaking, db: Session) -> UndertakingResponse:
    app = db.query(Application).filter(Application.id == u.application_id).first()
    inst = db.query(Institution).filter(Institution.id == u.institution_id).first()
    now = utcnow()
    is_overdue = (u.due_at < now and u.status not in ["VERIFIED", "SUBMITTED"])

    return UndertakingResponse(
        id=u.id,
        application_id=u.application_id,
        app_no=app.app_no if app else None,
        institution_id=u.institution_id,
        institution_name=inst.name if inst else "Unknown",
        title=u.title,
        description=u.description,
        due_at=u.due_at,
        status=u.status,
        evidence_document_id=u.evidence_document_id,
        evidence_notes=u.evidence_notes,
        verified_by=u.verified_by,
        verified_at=u.verified_at,
        created_at=u.created_at,
        is_overdue=is_overdue
    )

def enrich_doc_response(d: Document) -> DocumentResponse:
    days_left = (d.valid_until - utcnow()).days if d.valid_until else None
    return DocumentResponse(
        id=d.id,
        institution_id=d.institution_id,
        application_id=d.application_id,
        undertaking_id=d.undertaking_id,
        doc_type=d.doc_type,
        file_name=d.file_name,
        storage_key=d.storage_key,
        mime=d.mime,
        size=d.size,
        uploaded_by=d.uploaded_by,
        version_no=d.version_no,
        valid_from=d.valid_from,
        valid_until=d.valid_until,
        status=d.status,
        replaced_by_id=d.replaced_by_id,
        created_at=d.created_at,
        days_until_expiry=days_left
    )

# --- Undertakings Endpoints ---

@router.get("/undertakings", response_model=List[UndertakingResponse])
def list_undertakings(
    institution_id: Optional[str] = None,
    application_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    inst_filter = current_user.institution_id if current_user.role == UserRole.INSTITUTION else institution_id
    unds = ComplianceService.get_undertakings(
        db,
        institution_id=inst_filter,
        application_id=application_id,
        status_filter=status
    )
    return [enrich_undertaking(u, db) for u in unds]

@router.post("/undertakings/{id}/submit", response_model=UndertakingResponse)
def submit_undertaking_evidence(
    id: str,
    req: UndertakingEvidenceSubmit,
    current_user: User = Depends(require_role([UserRole.INSTITUTION])),
    db: Session = Depends(get_db)
):
    u = ComplianceService.submit_evidence(db, id, req, current_user)
    return enrich_undertaking(u, db)

@router.post("/undertakings/{id}/verify", response_model=UndertakingResponse)
def verify_undertaking(
    id: str,
    req: UndertakingVerify,
    current_user: User = Depends(require_role([UserRole.AUTHORISED_OFFICIAL, UserRole.ADMIN, UserRole.SCRUTINY_OFFICER])),
    db: Session = Depends(get_db)
):
    u = ComplianceService.verify_undertaking(db, id, req, current_user)
    return enrich_undertaking(u, db)

# --- Documents Endpoints ---

@router.post("/documents", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Form(...),
    institution_id: Optional[str] = Form(None),
    application_id: Optional[str] = Form(None),
    undertaking_id: Optional[str] = Form(None),
    valid_from: Optional[datetime] = Form(None),
    valid_until: Optional[datetime] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    inst_id = current_user.institution_id if current_user.role == UserRole.INSTITUTION else institution_id
    if not inst_id:
        raise HTTPException(status_code=400, detail={"code": "INSTITUTION_REQUIRED", "message": "Institution ID must be specified"})

    doc = await ComplianceService.upload_document(
        db=db,
        file=file,
        institution_id=inst_id,
        doc_type=doc_type,
        uploaded_by=current_user,
        application_id=application_id,
        undertaking_id=undertaking_id,
        valid_from=valid_from,
        valid_until=valid_until
    )
    return enrich_doc_response(doc)

@router.get("/documents", response_model=List[DocumentResponse])
def list_documents(
    institution_id: Optional[str] = None,
    application_id: Optional[str] = None,
    doc_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Document)
    if current_user.role == UserRole.INSTITUTION:
        query = query.filter(Document.institution_id == current_user.institution_id)
    elif institution_id:
        query = query.filter(Document.institution_id == institution_id)

    if application_id:
        query = query.filter(Document.application_id == application_id)
    if doc_type:
        query = query.filter(Document.doc_type == doc_type)

    docs = query.order_by(Document.created_at.desc()).all()
    return [enrich_doc_response(d) for d in docs]

@router.get("/documents/{id}/download")
def download_document(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc, filepath = ComplianceService.get_document_for_download(db, id, current_user)
    return FileResponse(
        path=filepath,
        filename=doc.file_name,
        media_type=doc.mime
    )

@router.post("/documents/{id}/renew", response_model=DocumentResponse)
async def renew_document(
    id: str,
    file: UploadFile = File(...),
    valid_from: datetime = Form(...),
    valid_until: datetime = Form(...),
    current_user: User = Depends(require_role([UserRole.INSTITUTION, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    req = DocumentRenewRequest(valid_from=valid_from, valid_until=valid_until)
    new_doc = await ComplianceService.renew_document(db, id, req, file, current_user)
    return enrich_doc_response(new_doc)

@router.get("/documents/expiring", response_model=List[DocumentResponse])
def list_expiring_documents(
    days: int = Query(30, ge=1, le=365),
    institution_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    inst_id = current_user.institution_id if current_user.role == UserRole.INSTITUTION else institution_id
    docs = ComplianceService.get_expiring_documents(db, days=days, institution_id=inst_id)
    return [enrich_doc_response(d) for d in docs]
