import csv
import io
from typing import Optional
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from app.core.database import get_db, utcnow
from app.core.deps import get_current_user
from app.models.workflow import Application, Task
from app.models.institution import Institution
from app.models.compliance import Undertaking, Document
from app.models.user import User

router = APIRouter(prefix="/reports", tags=["Reports & Export"])

@router.get("/export")
def export_reports_csv(
    report_type: str = Query("pendency", pattern="^(pendency|overdue|compliance|expiring_documents)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    output = io.StringIO()
    writer = csv.writer(output)

    if report_type == "pendency":
        writer.writerow(["Application No", "Institution", "Programme", "Status", "Submitted At", "Current Owner"])
        apps = db.query(Application).all()
        for a in apps:
            inst = db.query(Institution).filter(Institution.id == a.institution_id).first()
            owner = db.query(User).filter(User.id == a.current_owner_id).first() if a.current_owner_id else None
            writer.writerow([a.app_no, inst.name if inst else "", a.programme, a.status, a.submitted_at or "", owner.full_name if owner else ""])

    elif report_type == "overdue":
        writer.writerow(["Task ID", "Application No", "Task Type", "Role", "Due Date", "Status", "Escalation Level"])
        tasks = db.query(Task).filter(Task.status.in_(["OVERDUE", "ESCALATED"])).all()
        for t in tasks:
            app = db.query(Application).filter(Application.id == t.application_id).first()
            writer.writerow([t.id, app.app_no if app else "", t.type, t.role, t.due_at, t.status, t.escalation_level])

    elif report_type == "compliance":
        writer.writerow(["Undertaking ID", "Application No", "Title", "Due Date", "Status", "Verified At"])
        unds = db.query(Undertaking).all()
        for u in unds:
            app = db.query(Application).filter(Application.id == u.application_id).first()
            writer.writerow([u.id, app.app_no if app else "", u.title, u.due_at, u.status, u.verified_at or ""])

    elif report_type == "expiring_documents":
        writer.writerow(["Document ID", "Institution", "Document Type", "File Name", "Valid Until", "Status"])
        docs = db.query(Document).filter(Document.status.in_(["EXPIRING", "EXPIRED"])).all()
        for d in docs:
            inst = db.query(Institution).filter(Institution.id == d.institution_id).first()
            writer.writerow([d.id, inst.name if inst else "", d.doc_type, d.file_name, d.valid_until or "", d.status])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=watchtower_{report_type}_report.csv"}
    )
