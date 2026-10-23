import os
import uuid
import shutil
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Tuple
from fastapi import HTTPException, status, UploadFile
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import utcnow
from app.core.audit import log_audit
from app.models.workflow import Application
from app.models.compliance import Undertaking, Document
from app.models.institution import Institution
from app.models.user import User, UserRole
from app.workflow.engine import WorkflowEngine
from app.schemas.compliance import (
    UndertakingCreate,
    UndertakingEvidenceSubmit,
    UndertakingVerify,
    DocumentRenewRequest
)

class ComplianceService:
    @staticmethod
    def get_undertakings(
        db: Session,
        institution_id: Optional[str] = None,
        application_id: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> List[Undertaking]:
        query = db.query(Undertaking)
        if institution_id:
            query = query.filter(Undertaking.institution_id == institution_id)
        if application_id:
            query = query.filter(Undertaking.application_id == application_id)
        if status_filter:
            query = query.filter(Undertaking.status == status_filter)
        return query.order_by(Undertaking.due_at.asc()).all()

    @staticmethod
    def create_undertaking(
        db: Session,
        application_id: str,
        data: UndertakingCreate,
        actor: User
    ) -> Undertaking:
        app = db.query(Application).filter(Application.id == application_id).first()
        if not app:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Application not found"})

        undertaking = Undertaking(
            application_id=app.id,
            institution_id=app.institution_id,
            title=data.title,
            description=data.description,
            due_at=utcnow() + timedelta(days=data.due_days),
            status="PENDING"
        )
        db.add(undertaking)
        db.commit()
        db.refresh(undertaking)

        log_audit(
            db=db,
            action="CREATE_UNDERTAKING",
            entity_type="UNDERTAKING",
            entity_id=undertaking.id,
            actor_id=actor.id
        )
        return undertaking

    @staticmethod
    def submit_evidence(
        db: Session,
        undertaking_id: str,
        data: UndertakingEvidenceSubmit,
        user: User
    ) -> Undertaking:
        und = db.query(Undertaking).filter(Undertaking.id == undertaking_id).first()
        if not und:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Undertaking not found"})

        if user.role == UserRole.INSTITUTION and und.institution_id != user.institution_id:
            raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "Access denied"})

        und.evidence_document_id = data.evidence_document_id
        und.evidence_notes = data.evidence_notes
        und.status = "SUBMITTED"
        db.commit()
        db.refresh(und)

        log_audit(
            db=db,
            action="SUBMIT_UNDERTAKING_EVIDENCE",
            entity_type="UNDERTAKING",
            entity_id=und.id,
            actor_id=user.id
        )
        return und

    @staticmethod
    def verify_undertaking(
        db: Session,
        undertaking_id: str,
        data: UndertakingVerify,
        official: User
    ) -> Undertaking:
        if official.role not in [UserRole.AUTHORISED_OFFICIAL, UserRole.ADMIN, UserRole.SCRUTINY_OFFICER]:
            raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "Unauthorized to verify"})

        und = db.query(Undertaking).filter(Undertaking.id == undertaking_id).first()
        if not und:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Undertaking not found"})

        now = utcnow()
        if data.status == "VERIFIED":
            und.status = "VERIFIED"
            und.verified_by = official.id
            und.verified_at = now
        elif data.status == "REJECTED":
            und.status = "REJECTED"
            if data.new_due_days:
                und.due_at = now + timedelta(days=data.new_due_days)
        db.commit()
        db.refresh(und)

        log_audit(
            db=db,
            action="VERIFY_UNDERTAKING",
            entity_type="UNDERTAKING",
            entity_id=und.id,
            actor_id=official.id,
            after_state={"status": data.status}
        )
        return und

    @staticmethod
    def close_application_compliance(
        db: Session,
        application_id: str,
        official: User
    ) -> Application:
        """Rule 3.5: Closing blocked while any undertaking is not VERIFIED"""
        app = db.query(Application).filter(Application.id == application_id).first()
        if not app:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Application not found"})

        unverified = db.query(Undertaking).filter(
            Undertaking.application_id == application_id,
            Undertaking.status != "VERIFIED"
        ).count()

        if unverified > 0:
            raise HTTPException(
                status_code=400,
                detail={"code": "UNRESOLVED_UNDERTAKINGS", "message": f"Cannot close application: {unverified} undertakings are not yet verified"}
            )

        WorkflowEngine.transition(
            db,
            app,
            "CLOSED",
            actor=official,
            outcome="All compliance conditions and undertakings verified"
        )
        return app

    # --- Document Management (3.6 - 3.11) ---

    @staticmethod
    async def upload_document(
        db: Session,
        file: UploadFile,
        institution_id: str,
        doc_type: str,
        uploaded_by: User,
        application_id: Optional[str] = None,
        undertaking_id: Optional[str] = None,
        valid_from: Optional[datetime] = None,
        valid_until: Optional[datetime] = None
    ) -> Document:
        # Check extension
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail={"code": "FILE_REJECTED", "message": f"File type '{ext}' is not permitted. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"}
            )

        # Read file & check size
        contents = await file.read()
        size_bytes = len(contents)
        if size_bytes > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail={"code": "FILE_TOO_LARGE", "message": f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB} MB"}
            )

        # Versioning: check if existing document with same doc_type exists for institution / application
        existing = db.query(Document).filter(
            Document.institution_id == institution_id,
            Document.doc_type == doc_type,
            Document.application_id == application_id
        ).order_by(Document.version_no.desc()).first()
        version_no = (existing.version_no + 1) if existing else 1

        # Save to storage with randomized key
        storage_filename = f"{uuid.uuid4().hex}{ext}"
        storage_filepath = os.path.join(settings.STORAGE_PATH, storage_filename)
        with open(storage_filepath, "wb") as f:
            f.write(contents)

        # Compute validity status
        now = utcnow()
        doc_status = "VALID"
        if valid_until:
            if valid_until < now:
                doc_status = "EXPIRED"
            elif valid_until < (now + timedelta(days=30)):
                doc_status = "EXPIRING"

        doc = Document(
            institution_id=institution_id,
            application_id=application_id,
            undertaking_id=undertaking_id,
            doc_type=doc_type,
            file_name=file.filename,
            storage_key=storage_filename,
            mime=file.content_type or "application/octet-stream",
            size=size_bytes,
            uploaded_by=uploaded_by.id,
            version_no=version_no,
            valid_from=valid_from,
            valid_until=valid_until,
            status=doc_status
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        log_audit(
            db=db,
            action="UPLOAD_DOCUMENT",
            entity_type="DOCUMENT",
            entity_id=doc.id,
            actor_id=uploaded_by.id,
            after_state={"doc_type": doc_type, "version": version_no, "file_name": file.filename}
        )
        return doc

    @staticmethod
    def renew_document(
        db: Session,
        old_doc_id: str,
        data: DocumentRenewRequest,
        new_file: UploadFile,
        user: User
    ) -> Document:
        old_doc = db.query(Document).filter(Document.id == old_doc_id).first()
        if not old_doc:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Original document not found"})

        # Upload new document
        new_doc = ComplianceService.upload_document(
            db=db,
            file=new_file,
            institution_id=old_doc.institution_id,
            doc_type=old_doc.doc_type,
            uploaded_by=user,
            application_id=old_doc.application_id,
            valid_from=data.valid_from,
            valid_until=data.valid_until
        )

        # Mark old document RENEWED
        old_doc.status = "RENEWED"
        old_doc.replaced_by_id = new_doc.id
        db.commit()

        log_audit(
            db=db,
            action="RENEW_DOCUMENT",
            entity_type="DOCUMENT",
            entity_id=old_doc.id,
            actor_id=user.id,
            after_state={"replaced_by_id": new_doc.id}
        )
        return new_doc

    @staticmethod
    def get_document_for_download(
        db: Session,
        doc_id: str,
        user: User
    ) -> Tuple[Document, str]:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Document not found"})

        if user.role == UserRole.INSTITUTION and doc.institution_id != user.institution_id:
            raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "Unauthorized to access this document"})

        filepath = os.path.join(settings.STORAGE_PATH, doc.storage_key)
        if not os.path.exists(filepath):
            # Create a placeholder dummy file if storage file missing in dev demo
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w") as f:
                f.write(f"DEMO DOCUMENT CONTENT for {doc.file_name}")

        log_audit(
            db=db,
            action="DOWNLOAD_DOCUMENT",
            entity_type="DOCUMENT",
            entity_id=doc.id,
            actor_id=user.id
        )
        return doc, filepath

    @staticmethod
    def get_expiring_documents(
        db: Session,
        days: int = 30,
        institution_id: Optional[str] = None
    ) -> List[Document]:
        now = utcnow()
        cutoff = now + timedelta(days=days)
        query = db.query(Document).filter(
            Document.valid_until.is_not(None),
            Document.valid_until <= cutoff,
            Document.status.in_(["VALID", "EXPIRING", "EXPIRED"])
        )
        if institution_id:
            query = query.filter(Document.institution_id == institution_id)
        return query.order_by(Document.valid_until.asc()).all()
