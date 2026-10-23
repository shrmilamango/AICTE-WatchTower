from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db, utcnow
from app.core.deps import get_current_user
from app.models.workflow import Application, Task
from app.models.institution import Institution
from app.models.evc import EvcVisit
from app.models.compliance import Undertaking, Document
from app.models.user import User, UserRole
from app.models.risk import RiskScore
from app.schemas.alert import DashboardSummary

router = APIRouter(prefix="/dashboard", tags=["Dashboard & Analytics"])

@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    region: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rule 5.1: Live database counts. Done when every card equals count of drill-down list."""
    app_query = db.query(Application)
    doc_query = db.query(Document)
    und_query = db.query(Undertaking)
    evc_query = db.query(EvcVisit)
    task_query = db.query(Task)

    inst_approved = 0
    inst_deficiencies = 0
    my_open = 0
    my_overdue = 0
    evc_sched = 0
    evc_rep_pending = 0
    committee_rev = 0

    if current_user.role == UserRole.INSTITUTION:
        app_query = app_query.filter(Application.institution_id == current_user.institution_id)
        doc_query = doc_query.filter(Document.institution_id == current_user.institution_id)
        und_query = und_query.filter(Undertaking.institution_id == current_user.institution_id)
        inst_approved = app_query.filter(Application.status.in_(["APPROVED", "APPROVED_WITH_CONDITIONS"])).count()
        inst_deficiencies = app_query.filter(Application.status == "DEFICIENCY_RAISED").count()
    else:
        if region:
            app_query = app_query.join(Institution, Application.institution_id == Institution.id).filter(Institution.region == region)
        
        # Officer personal tasks
        my_open = db.query(Task).filter(Task.assigned_to == current_user.id, Task.status == "OPEN").count()
        my_overdue = db.query(Task).filter(Task.assigned_to == current_user.id, Task.status.in_(["OVERDUE", "ESCALATED"])).count()
        
        # EVC coordinator metrics
        evc_sched = db.query(EvcVisit).filter(EvcVisit.status == "SCHEDULED").count()
        evc_rep_pending = db.query(EvcVisit).filter(EvcVisit.status == "COMPLETED").count()
        
        # Committee & deficiency metrics
        committee_rev = db.query(Application).filter(Application.status == "COMMITTEE_REVIEW").count()
        inst_deficiencies = db.query(Application).filter(Application.status == "DEFICIENCY_RAISED").count()

    total_apps = app_query.count()
    under_scrutiny = app_query.filter(Application.status.in_(["UNDER_SCRUTINY", "RESUBMITTED"])).count()
    
    # EVCs awaiting scheduling
    evc_awaiting = evc_query.filter(EvcVisit.status == "REQUIRED").count()

    # Overdue applications (having at least 1 overdue or escalated task)
    overdue_apps = db.query(Application).join(Task, Application.id == Task.application_id)\
        .filter(Task.status.in_(["OVERDUE", "ESCALATED"])).distinct().count()

    # Compliance pending
    compliance_pending = und_query.filter(Undertaking.status.in_(["PENDING", "OVERDUE", "SUBMITTED"])).count()

    # Documents expiring soon (<= 30 days or expired)
    expiring_docs = doc_query.filter(Document.status.in_(["EXPIRING", "EXPIRED"])).count()

    return DashboardSummary(
        total_applications=total_apps,
        under_scrutiny=under_scrutiny,
        evc_awaiting_scheduling=evc_awaiting,
        overdue_applications=overdue_apps,
        compliance_pending=compliance_pending,
        documents_expiring_soon=expiring_docs,
        institution_approved=inst_approved,
        institution_deficiencies=inst_deficiencies,
        my_open_tasks=my_open,
        my_overdue_tasks=my_overdue,
        evc_scheduled=evc_sched,
        evc_reports_pending=evc_rep_pending,
        committee_review_count=committee_rev
    )

@router.get("/pendency")
def get_pendency_analysis(
    group_by: str = Query("stage", pattern="^(stage|region|official|age)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rule 5.2: Pendency breakdown by stage, region, official, and age bucket."""
    now = utcnow()
    
    if group_by == "stage":
        results = db.query(Application.status, func.count(Application.id))\
            .group_by(Application.status).all()
        return [{"label": r[0], "count": r[1]} for r in results]

    elif group_by == "region":
        results = db.query(Institution.region, func.count(Application.id))\
            .join(Application, Institution.id == Application.institution_id)\
            .group_by(Institution.region).all()
        return [{"label": r[0] or "Unknown", "count": r[1]} for r in results]

    elif group_by == "official":
        results = db.query(User.full_name, func.count(Task.id))\
            .join(Task, User.id == Task.assigned_to)\
            .filter(Task.status.in_(["OPEN", "OVERDUE", "ESCALATED"]))\
            .group_by(User.full_name).all()
        return [{"label": r[0], "count": r[1]} for r in results]

    elif group_by == "age":
        # Age buckets: 0-7, 8-15, 16-30, 30+ days
        apps = db.query(Application).filter(Application.submitted_at.is_not(None)).all()
        buckets = {"0-7 Days": 0, "8-15 Days": 0, "16-30 Days": 0, "30+ Days": 0}
        for a in apps:
            days = (now - a.submitted_at).days
            if days <= 7:
                buckets["0-7 Days"] += 1
            elif days <= 15:
                buckets["8-15 Days"] += 1
            elif days <= 30:
                buckets["16-30 Days"] += 1
            else:
                buckets["30+ Days"] += 1
        return [{"label": k, "count": v} for k, v in buckets.items()]

@router.get("/officer-workload")
def get_officer_workload(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rule 5.6: Officer workload showing open, overdue, and escalated counts."""
    officers = db.query(User).filter(
        User.role.in_([UserRole.SCRUTINY_OFFICER, UserRole.EVC_COORDINATOR, UserRole.COMMITTEE_MEMBER, UserRole.AUTHORISED_OFFICIAL])
    ).all()
    
    out = []
    for off in officers:
        open_cnt = db.query(Task).filter(Task.assigned_to == off.id, Task.status == "OPEN").count()
        overdue_cnt = db.query(Task).filter(Task.assigned_to == off.id, Task.status == "OVERDUE").count()
        escalated_cnt = db.query(Task).filter(Task.assigned_to == off.id, Task.status == "ESCALATED").count()
        out.append({
            "officer_id": off.id,
            "officer_name": off.full_name,
            "role": off.role,
            "region": off.region,
            "open_tasks": open_cnt,
            "overdue_tasks": overdue_cnt,
            "escalated_tasks": escalated_cnt,
            "total_active": open_cnt + overdue_cnt + escalated_cnt
        })
    return out
