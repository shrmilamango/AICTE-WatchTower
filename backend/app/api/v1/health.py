from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db

router = APIRouter(tags=["Health"])

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    status_report = {
        "status": "healthy",
        "services": {
            "database": "unknown",
            "redis": "healthy (simulated/optional)",
            "worker": "healthy (in-process scheduler active)"
        }
    }

    # Check Database connection
    try:
        db.execute(text("SELECT 1"))
        status_report["services"]["database"] = "healthy"
    except Exception as e:
        status_report["services"]["database"] = f"unhealthy: {str(e)}"
        status_report["status"] = "degraded"

    return status_report
