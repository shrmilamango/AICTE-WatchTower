from typing import Optional, Any
from sqlalchemy.orm import Session
import json
from app.core.database import utcnow

def log_audit(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: str,
    actor_id: Optional[str] = None,
    before_state: Optional[dict[str, Any]] = None,
    after_state: Optional[dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    commit: bool = True
):
    from app.models.audit import AuditLog
    
    audit_entry = AuditLog(
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_state=before_state,
        after_state=after_state,
        ip_address=ip_address,
        created_at=utcnow()
    )
    db.add(audit_entry)
    if commit:
        db.commit()
    return audit_entry
