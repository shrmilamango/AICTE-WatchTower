from typing import Any, Optional
from sqlalchemy.orm import Session
from app.core.audit import log_audit
from app.models.config import ConfigRule
from app.models.user import User

DEFAULT_CONFIGS = {
    "workflow_sla_days": {
        "description": "Default SLA days per workflow stage",
        "value": {
            "SUBMITTED": 2,
            "UNDER_SCRUTINY": 7,
            "DEFICIENCY_RAISED": 7,
            "RESUBMITTED": 3,
            "EVC_REQUIRED": 5,
            "EVC_SCHEDULED": 10,
            "EVC_COMPLETED": 3,
            "COMMITTEE_REVIEW": 7,
            "DECISION_PENDING": 5
        }
    },
    "reminder_offsets": {
        "description": "Reminder day offsets before due date",
        "value": {
            "tasks": [-2, -1, 0],
            "undertakings": [-15, -7, 0],
            "documents": [-30, -7, 0]
        }
    },
    "escalation_thresholds": {
        "description": "Days overdue required to trigger escalation tiers",
        "value": {
            "level_1_days": 2,
            "level_2_days": 5
        }
    },
    "validity_required_doc_types": {
        "description": "Document types that require validity tracking and renewal alerts",
        "value": ["LAND_LEASE", "FIRE_SAFETY_NOC", "AFFILIATION_DOC", "POLLUTION_NOC", "BUILDING_SAFETY"]
    },
    "risk_rule_weights": {
        "description": "Point weights for delay-risk engine factors",
        "value": {
            "sla_over_70": 20,
            "task_overdue": 35,
            "two_deficiencies": 15,
            "evc_unscheduled_late": 20,
            "undertaking_due_soon": 15,
            "document_expiring": 10,
            "officer_overloaded": 10
        }
    }
}

class ConfigService:
    @staticmethod
    def init_default_configs(db: Session):
        for key, item in DEFAULT_CONFIGS.items():
            existing = db.query(ConfigRule).filter(ConfigRule.key == key).first()
            if not existing:
                rule = ConfigRule(
                    key=key,
                    value=item["value"],
                    description=item["description"],
                    version=1
                )
                db.add(rule)
        db.commit()

    @staticmethod
    def get_value(db: Session, key: str) -> Optional[Any]:
        rule = db.query(ConfigRule).filter(ConfigRule.key == key).first()
        if rule:
            return rule.value
        return DEFAULT_CONFIGS.get(key, {}).get("value")

    @staticmethod
    def update_config(db: Session, key: str, value: Any, actor: User, description: Optional[str] = None) -> ConfigRule:
        rule = db.query(ConfigRule).filter(ConfigRule.key == key).first()
        before_state = None
        if rule:
            before_state = {"value": rule.value, "version": rule.version}
            rule.value = value
            rule.version += 1
            if description:
                rule.description = description
            rule.updated_by = actor.id
        else:
            rule = ConfigRule(
                key=key,
                value=value,
                description=description or DEFAULT_CONFIGS.get(key, {}).get("description", ""),
                version=1,
                updated_by=actor.id
            )
            db.add(rule)
        db.commit()
        db.refresh(rule)

        log_audit(
            db=db,
            action="UPDATE_CONFIG",
            entity_type="CONFIG_RULE",
            entity_id=rule.id,
            actor_id=actor.id,
            before_state=before_state,
            after_state={"value": value, "version": rule.version}
        )
        return rule
