from typing import List, Optional
import csv
import io
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.audit import AuditLog
from app.models.user import User, UserRole
from app.schemas.alert import AuditLogResponse

router = APIRouter(prefix="/audit-logs", tags=["Audit Trail"])

def enrich_audit(log: AuditLog, db: Session) -> AuditLogResponse:
    actor = db.query(User).filter(User.id == log.actor_id).first() if log.actor_id else None
    return AuditLogResponse(
        id=log.id,
        actor_id=log.actor_id,
        actor_name=actor.full_name if actor else ("SYSTEM" if not log.actor_id else "Unknown"),
        action=log.action,
        entity_type=log.entity_type,
        entity_id=log.entity_id,
        before_state=log.before_state,
        after_state=log.after_state,
        ip_address=log.ip_address,
        created_at=log.created_at
    )

@router.get("", response_model=List[AuditLogResponse])
def get_audit_logs(
    actor_id: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(require_role([UserRole.AUDITOR, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    query = db.query(AuditLog)
    if actor_id:
        query = query.filter(AuditLog.actor_id == actor_id)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if entity_id:
        query = query.filter(AuditLog.entity_id == entity_id)
    if action:
        query = query.filter(AuditLog.action == action)
        
    logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    return [enrich_audit(l, db) for l in logs]

@router.get("/export")
def export_audit_logs_csv(
    entity_type: Optional[str] = None,
    current_user: User = Depends(require_role([UserRole.AUDITOR, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    query = db.query(AuditLog)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    logs = query.order_by(AuditLog.created_at.desc()).limit(1000).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Timestamp (UTC)", "Actor ID", "Action", "Entity Type", "Entity ID", "IP Address"])
    for l in logs:
        writer.writerow([l.id, l.created_at.isoformat(), l.actor_id or "SYSTEM", l.action, l.entity_type, l.entity_id, l.ip_address or ""])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=watchtower_audit_trail.csv"}
    )
