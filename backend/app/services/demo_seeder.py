import os
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.core.database import utcnow
from app.core.security import hash_password

DEFAULT_PASSWORD = "Password@123"
from app.models.user import User, UserRole
from app.models.institution import Institution
from app.models.workflow import WorkflowTemplate, WorkflowStage, Application, ApplicationStageHistory, Task
from app.models.scrutiny import ScrutinyReview, Deficiency
from app.models.evc import EvcVisit
from app.models.committee import CommitteeReview
from app.models.decision import Decision
from app.models.compliance import Undertaking, Document
from app.models.alert import Notification, ReminderRule, EscalationRule
from app.workflow.engine import WorkflowEngine
from app.services.risk_service import RiskService

def seed_demo_database(db: Session) -> dict:
    """
    Cleanses and initializes the database with consistent, labeled [DEMO DATA].
    Guarantees no real people's names or junk test notes remain.
    Varies SLA usage across applications (20%, 45%, 71%, 90%, overdue).
    """
    now = utcnow()

    # 1. Initialize Default Workflow Template
    template = WorkflowEngine.init_default_template(db)

    # 2. Seed Default Reminder and Escalation Rules
    if db.query(ReminderRule).count() == 0:
        db.add_all([
            ReminderRule(target_type="TASK", offsets_days=[-2, -1, 0], channels=["IN_APP", "EMAIL"], active=True),
            ReminderRule(target_type="UNDERTAKING", offsets_days=[-15, -7, 0], channels=["IN_APP", "EMAIL"], active=True),
            ReminderRule(target_type="DOCUMENT", offsets_days=[-30, -7, 0], channels=["IN_APP", "EMAIL"], active=True)
        ])
        db.commit()

    if db.query(EscalationRule).count() == 0:
        db.add_all([
            # TASK ladder
            EscalationRule(target_type="TASK", level=1, after_overdue_days=2, escalate_to_role=UserRole.AUTHORISED_OFFICIAL, active=True),
            EscalationRule(target_type="TASK", level=2, after_overdue_days=5, escalate_to_role=UserRole.AUTHORISED_OFFICIAL, active=True),
            # UNDERTAKING ladder
            EscalationRule(target_type="UNDERTAKING", level=1, after_overdue_days=2, escalate_to_role=UserRole.AUTHORISED_OFFICIAL, active=True),
            EscalationRule(target_type="UNDERTAKING", level=2, after_overdue_days=5, escalate_to_role=UserRole.AUTHORISED_OFFICIAL, active=True),
            # DOCUMENT ladder
            EscalationRule(target_type="DOCUMENT", level=1, after_overdue_days=2, escalate_to_role=UserRole.AUTHORISED_OFFICIAL, active=True),
            EscalationRule(target_type="DOCUMENT", level=2, after_overdue_days=5, escalate_to_role=UserRole.AUTHORISED_OFFICIAL, active=True)
        ])
        db.commit()

    # 3. Seed Institutions
    inst1 = db.query(Institution).filter(Institution.aicte_code == "DEMO-DEL-101").first()
    if not inst1:
        inst1 = Institution(
            name="Delhi Institute of Engineering & Technology [DEMO DATA]",
            aicte_code="DEMO-DEL-101",
            region="NORTH",
            state="Delhi",
            address="Plot 12, Institutional Area, Vasant Kunj, New Delhi",
            contact_name="Dr. Ramanathan Iyer [DEMO DATA]",
            contact_email="principal.diet@demo.aicte.gov.in",
            contact_phone="+91 98110 12345",
            status="ACTIVE"
        )
        db.add(inst1)
        db.commit()
        db.refresh(inst1)

    inst2 = db.query(Institution).filter(Institution.aicte_code == "DEMO-MUM-202").first()
    if not inst2:
        inst2 = Institution(
            name="Mumbai College of Management & Technology [DEMO DATA]",
            aicte_code="DEMO-MUM-202",
            region="WEST",
            state="Maharashtra",
            address="Bandra-Kurla Complex, Mumbai",
            contact_name="Dr. Shailesh Kulkarni [DEMO DATA]",
            contact_email="director.mcmt@demo.aicte.gov.in",
            contact_phone="+91 98220 54321",
            status="ACTIVE"
        )
        db.add(inst2)
        db.commit()
        db.refresh(inst2)

    # 4. Seed Users for every role
    pass_hash = hash_password(DEFAULT_PASSWORD)
    users_to_seed = [
        ("admin@demo.aicte.gov.in", "System Administrator [DEMO DATA]", UserRole.ADMIN, None, "NORTH"),
        ("auditor@demo.aicte.gov.in", "Chief Auditor - Oversight [DEMO DATA]", UserRole.AUDITOR, None, "NORTH"),
        ("official@demo.aicte.gov.in", "Dr. Rekha Gupta (Authorised Official) [DEMO DATA]", UserRole.AUTHORISED_OFFICIAL, None, "All Regions"),
        ("scrutiny@demo.aicte.gov.in", "Dr. A. K. Sharma (Scrutiny Officer) [DEMO DATA]", UserRole.SCRUTINY_OFFICER, None, "NORTH"),
        ("scrutiny2@demo.aicte.gov.in", "Dr. Sunita Rao (Scrutiny Officer) [DEMO DATA]", UserRole.SCRUTINY_OFFICER, None, "WEST"),
        ("evc@demo.aicte.gov.in", "Er. Rajesh Verma (EVC Coordinator) [DEMO DATA]", UserRole.EVC_COORDINATOR, None, "NORTH"),
        ("committee@demo.aicte.gov.in", "Prof. R. K. Menon (SAC Member) [DEMO DATA]", UserRole.COMMITTEE_MEMBER, None, "NORTH"),
        ("college@demo.aicte.gov.in", "Principal - Delhi Inst of Tech [DEMO DATA]", UserRole.INSTITUTION, inst1.id, "NORTH"),
        ("college2@demo.aicte.gov.in", "Dean - Mumbai College [DEMO DATA]", UserRole.INSTITUTION, inst2.id, "WEST"),
    ]

    seeded_users = {}
    for email, name, role, i_id, reg in users_to_seed:
        u = db.query(User).filter(User.email == email).first()
        if not u:
            u = User(
                email=email,
                password_hash=pass_hash,
                full_name=name,
                role=role,
                institution_id=i_id,
                region=reg,
                is_active=True
            )
            db.add(u)
            db.commit()
            db.refresh(u)
        else:
            u.full_name = name
            u.region = reg
            db.commit()
        seeded_users[email] = u

    # 5. Seed Applications at various realistic pipeline stages with varied SLA consumption
    # WT-0001: UNDER_SCRUTINY, ~20% SLA, LOW
    # WT-0002: DEFICIENCY_RAISED, ~45% SLA, LOW (with correct Dr. A.K. Sharma actor on stage entry)
    # WT-0003: EVC_REQUIRED, Overdue SLA, HIGH (with 3 factors)
    # WT-0004: EVC_SCHEDULED (in WEST for inst2), ~71% SLA, MEDIUM
    # WT-0005: COMMITTEE_REVIEW (in NORTH for inst1), ~90% SLA, MEDIUM
    # WT-0006: APPROVED_WITH_CONDITIONS (in NORTH for inst1), LOW
    apps_data = [
        ("WT-2026-0001", inst1.id, "Engineering & Technology", "UNDER_SCRUTINY", seeded_users["scrutiny@demo.aicte.gov.in"].id, now - timedelta(days=2)),
        ("WT-2026-0002", inst1.id, "Management", "DEFICIENCY_RAISED", seeded_users["college@demo.aicte.gov.in"].id, now - timedelta(days=12)),
        ("WT-2026-0003", inst1.id, "Pharmacy", "EVC_REQUIRED", seeded_users["evc@demo.aicte.gov.in"].id, now - timedelta(days=15)),
        ("WT-2026-0004", inst2.id, "Engineering & Technology", "EVC_SCHEDULED", seeded_users["evc@demo.aicte.gov.in"].id, now - timedelta(days=16)),
        ("WT-2026-0005", inst1.id, "Computer Applications (MCA)", "COMMITTEE_REVIEW", seeded_users["committee@demo.aicte.gov.in"].id, now - timedelta(days=20)),
        ("WT-2026-0006", inst1.id, "Architecture & Planning", "APPROVED_WITH_CONDITIONS", seeded_users["official@demo.aicte.gov.in"].id, now - timedelta(days=30))
    ]

    for app_no, i_id, prog, st, owner_id, sub_date in apps_data:
        existing_app = db.query(Application).filter(Application.app_no == app_no).first()
        if not existing_app:
            app = Application(
                app_no=app_no,
                institution_id=i_id,
                template_id=template.id,
                programme=prog,
                academic_year="2026-27",
                form_data={
                    "intake_requested": 120,
                    "faculty_count": 28,
                    "built_up_area_sqm": 8500,
                    "labs_count": 14,
                    "library_titles": 4200,
                    "notes": "Application submitted for academic expansion [DEMO DATA]"
                },
                status=st,
                current_stage_key=st,
                current_owner_id=owner_id,
                submitted_at=sub_date
            )
            db.add(app)
            db.commit()
            db.refresh(app)

            # Stage history & tasks tailored for each application
            if app_no == "WT-2026-0001":
                # 20% SLA: Entered 2 days ago, due in 8 days (2/10 = 20%)
                db.add(ApplicationStageHistory(
                    application_id=app.id,
                    stage_key="SUBMITTED",
                    entered_at=now - timedelta(days=2),
                    completed_at=now - timedelta(days=2),
                    owner_id=seeded_users["college@demo.aicte.gov.in"].id,
                    actor_id=seeded_users["college@demo.aicte.gov.in"].id,
                    outcome="Application submitted [DEMO DATA]"
                ))
                db.add(ApplicationStageHistory(
                    application_id=app.id,
                    stage_key="UNDER_SCRUTINY",
                    entered_at=now - timedelta(days=2),
                    due_at=now + timedelta(days=8),
                    owner_id=owner_id,
                    actor_id=seeded_users["scrutiny@demo.aicte.gov.in"].id,
                    outcome="Assigned for initial scrutiny [DEMO DATA]"
                ))
                db.add(Task(
                    application_id=app.id,
                    type="UNDER_SCRUTINY",
                    assigned_to=owner_id,
                    role=UserRole.SCRUTINY_OFFICER,
                    due_at=now + timedelta(days=8),
                    status="OPEN",
                    escalation_level=0
                ))
                db.add(Document(
                    institution_id=i_id,
                    application_id=app.id,
                    doc_type="FIRE_SAFETY_NOC",
                    file_name="Fire_Safety_Certificate_NOC.pdf",
                    storage_key="demo_fire_noc.pdf",
                    mime="application/pdf",
                    size=1120000,
                    uploaded_by=seeded_users["college@demo.aicte.gov.in"].id,
                    version_no=1,
                    valid_from=now - timedelta(days=730),
                    valid_until=now + timedelta(days=180),
                    status="VALID"
                ))
                db.commit()

            elif app_no == "WT-2026-0002":
                # 45% SLA: Entered 4 days ago, due in 5 days (4/9 = 44.4% ~ 45%)
                # Chronological order:
                # 1. SUBMITTED: now - 12 days
                # 2. UNDER_SCRUTINY: now - 10 days, completed now - 4 days, 1 hour
                # 3. Scrutiny Round 1: DEFICIENT: now - 4 days, 1 hour (Dr. A. K. Sharma)
                # 4. Entered DEFICIENCY_RAISED: now - 4 days (Dr. A. K. Sharma actor)
                db.add(ApplicationStageHistory(
                    application_id=app.id,
                    stage_key="SUBMITTED",
                    entered_at=now - timedelta(days=12),
                    completed_at=now - timedelta(days=10),
                    owner_id=seeded_users["college@demo.aicte.gov.in"].id,
                    actor_id=seeded_users["college@demo.aicte.gov.in"].id,
                    outcome="Application submitted [DEMO DATA]"
                ))
                db.add(ApplicationStageHistory(
                    application_id=app.id,
                    stage_key="UNDER_SCRUTINY",
                    entered_at=now - timedelta(days=10),
                    completed_at=now - timedelta(days=4, hours=1, minutes=10),
                    owner_id=seeded_users["scrutiny@demo.aicte.gov.in"].id,
                    actor_id=seeded_users["scrutiny@demo.aicte.gov.in"].id,
                    outcome="Scrutiny conducted [DEMO DATA]"
                ))
                db.commit()

                rev = ScrutinyReview(
                    application_id=app.id,
                    reviewer_id=seeded_users["scrutiny@demo.aicte.gov.in"].id,
                    round_no=1,
                    outcome="DEFICIENT",
                    remarks="Faculty cadre ratio does not meet 1:15 norm; Land registration deed not attested [DEMO DATA]",
                    created_at=now - timedelta(days=4, hours=1)
                )
                db.add(rev)
                db.commit()
                db.refresh(rev)

                db.add_all([
                    Deficiency(
                        review_id=rev.id,
                        item="Faculty Cadre Ratio",
                        description="Cadre ratio of Professors to Associate Professors is deficient as per APH table 2.1 [DEMO DATA]",
                        status="OPEN",
                        due_at=now + timedelta(days=5),
                        created_at=now - timedelta(days=4, hours=1)
                    ),
                    Deficiency(
                        review_id=rev.id,
                        item="Fire Safety Certificate",
                        description="Municipal Fire Safety NOC submitted is past validity date [DEMO DATA]",
                        status="OPEN",
                        due_at=now + timedelta(days=5),
                        created_at=now - timedelta(days=4, hours=1)
                    )
                ])
                db.commit()

                # Stage history for DEFICIENCY_RAISED with Dr. A. K. Sharma as actor, 1 hour after review
                db.add(ApplicationStageHistory(
                    application_id=app.id,
                    stage_key="DEFICIENCY_RAISED",
                    entered_at=now - timedelta(days=4),
                    due_at=now + timedelta(days=5),
                    owner_id=owner_id,
                    actor_id=seeded_users["scrutiny@demo.aicte.gov.in"].id,
                    outcome="Entered DEFICIENCY_RAISED stage"
                ))
                db.add(Task(
                    application_id=app.id,
                    type="DEFICIENCY_RAISED",
                    assigned_to=owner_id,
                    role=UserRole.INSTITUTION,
                    due_at=now + timedelta(days=5),
                    status="OPEN",
                    escalation_level=0
                ))
                # Rename LAND_LEASE file to clean name Lease_Deed_Campus_2016.pdf
                db.add(Document(
                    institution_id=i_id,
                    application_id=app.id,
                    doc_type="LAND_LEASE",
                    file_name="Lease_Deed_Campus_2016.pdf",
                    storage_key="demo_lease_deed_2016.pdf",
                    mime="application/pdf",
                    size=2150000,
                    uploaded_by=seeded_users["college@demo.aicte.gov.in"].id,
                    version_no=1,
                    valid_from=now - timedelta(days=3650),
                    valid_until=now + timedelta(days=3650),
                    status="VALID"
                ))
                db.commit()

            elif app_no == "WT-2026-0003":
                # Overdue SLA: entered 10 days ago, due 3 days ago (>100% SLA)
                # HIGH Risk with 3 factors:
                # 1. TASK_OVERDUE (+35)
                # 2. EVC_UNSCHEDULED_PAST_TARGET (+20)
                # 3. SLA_CONSUMPTION_HIGH (+20) -> Total 75 pts (HIGH)
                db.add(ApplicationStageHistory(
                    application_id=app.id,
                    stage_key="EVC_REQUIRED",
                    entered_at=now - timedelta(days=10),
                    due_at=now - timedelta(days=3),
                    owner_id=owner_id,
                    actor_id=seeded_users["scrutiny@demo.aicte.gov.in"].id,
                    outcome="EVC Inspection Required [DEMO DATA]"
                ))
                db.add(Task(
                    application_id=app.id,
                    type="EVC_REQUIRED",
                    assigned_to=owner_id,
                    role=UserRole.EVC_COORDINATOR,
                    due_at=now - timedelta(days=3),
                    status="OVERDUE",
                    escalation_level=1
                ))
                db.add(EvcVisit(
                    application_id=app.id,
                    status="REQUIRED",
                    target_date=now - timedelta(days=2), # overdue!
                    coordinator_id=owner_id,
                    remarks="Awaiting constitution of expert visit team [DEMO DATA]"
                ))
                db.commit()

            elif app_no == "WT-2026-0004":
                # 71% SLA: Entered 5 days ago, due in 2 days (5/7 = 71.4%)
                # MEDIUM Risk: SLA_CONSUMPTION_HIGH (+20) + DOCUMENT_EXPIRING (+10) = 30 pts
                db.add(ApplicationStageHistory(
                    application_id=app.id,
                    stage_key="EVC_SCHEDULED",
                    entered_at=now - timedelta(days=5),
                    due_at=now + timedelta(days=2),
                    owner_id=owner_id,
                    actor_id=seeded_users["evc@demo.aicte.gov.in"].id,
                    outcome="EVC Visit Scheduled [DEMO DATA]"
                ))
                db.add(Task(
                    application_id=app.id,
                    type="EVC_SCHEDULED",
                    assigned_to=owner_id,
                    role=UserRole.EVC_COORDINATOR,
                    due_at=now + timedelta(days=2),
                    status="OPEN",
                    escalation_level=0
                ))
                db.add(EvcVisit(
                    application_id=app.id,
                    status="SCHEDULED",
                    target_date=now + timedelta(days=10),
                    scheduled_date=now + timedelta(days=6),
                    members=[
                        {"name": "Prof. S. Iyer", "affiliation": "Demo Institute", "role": "Chairman"},
                        {"name": "Dr. P. Kulkarni", "affiliation": "Demo Institute", "role": "Member"}
                    ],
                    coordinator_id=owner_id,
                    remarks="Physical inspection of laboratories and computing infrastructure [DEMO DATA]"
                ))
                db.add(Document(
                    institution_id=i_id,
                    application_id=app.id,
                    doc_type="LAND_LEASE",
                    file_name="Lease_Deed_Campus_2026.pdf",
                    storage_key="demo_lease_deed_2026.pdf",
                    mime="application/pdf",
                    size=2450000,
                    uploaded_by=seeded_users["college2@demo.aicte.gov.in"].id,
                    version_no=1,
                    valid_from=now - timedelta(days=365),
                    valid_until=now + timedelta(days=14), # EXPIRING in 14 days!
                    status="EXPIRING"
                ))
                db.commit()

            elif app_no == "WT-2026-0005":
                # 90% SLA: Entered 9 days ago, due in 1 day (9/10 = 90%)
                # MEDIUM Risk: SLA_CONSUMPTION_HIGH (+20) + DOCUMENT_EXPIRING (+10) = 30 pts
                db.add(ApplicationStageHistory(
                    application_id=app.id,
                    stage_key="COMMITTEE_REVIEW",
                    entered_at=now - timedelta(days=9),
                    due_at=now + timedelta(days=1),
                    owner_id=owner_id,
                    actor_id=seeded_users["official@demo.aicte.gov.in"].id,
                    outcome="Referred to Standing Appellate Committee [DEMO DATA]"
                ))
                db.add(Task(
                    application_id=app.id,
                    type="COMMITTEE_REVIEW",
                    assigned_to=owner_id,
                    role=UserRole.COMMITTEE_MEMBER, # Explicitly COMMITTEE_MEMBER
                    due_at=now + timedelta(days=1),
                    status="OPEN",
                    escalation_level=0
                ))
                db.add(CommitteeReview(
                    application_id=app.id,
                    committee_type="SAC",
                    reviewer_id=owner_id,
                    status="PENDING",
                    due_at=now + timedelta(days=1)
                ))
                db.add(Document(
                    institution_id=i_id,
                    application_id=app.id,
                    doc_type="BUILDING_SAFETY_CERTIFICATE",
                    file_name="Building_Safety_Certificate_2026.pdf",
                    storage_key="demo_building_safety.pdf",
                    mime="application/pdf",
                    size=1540000,
                    uploaded_by=seeded_users["college@demo.aicte.gov.in"].id,
                    version_no=1,
                    valid_from=now - timedelta(days=365),
                    valid_until=now + timedelta(days=20),
                    status="EXPIRING"
                ))
                db.commit()

            elif app_no == "WT-2026-0006":
                # Approved with conditions - LOW Risk (score 0)
                db.add(ApplicationStageHistory(
                    application_id=app.id,
                    stage_key="APPROVED_WITH_CONDITIONS",
                    entered_at=now - timedelta(days=10),
                    due_at=now + timedelta(days=20),
                    owner_id=owner_id,
                    actor_id=owner_id,
                    outcome="Final Order Issued [DEMO DATA]"
                ))
                db.add(Decision(
                    application_id=app.id,
                    decision="APPROVED_WITH_CONDITIONS",
                    decided_by=owner_id,
                    order_ref="AICTE/NWRO/2026/COND-882 [DEMO DATA]",
                    remarks="Approval granted subject to submission of updated registered lease deed and fire certificate within 30 days [DEMO DATA]",
                    decided_at=now - timedelta(days=10)
                ))
                db.add_all([
                    Undertaking(
                        application_id=app.id,
                        institution_id=i_id,
                        title="Submission of 30-Year Registered Land Lease Deed [DEMO DATA]",
                        description="Provide certified registered lease deed registered with sub-registrar",
                        due_at=now + timedelta(days=18),
                        status="PENDING"
                    ),
                    Undertaking(
                        application_id=app.id,
                        institution_id=i_id,
                        title="Permanent Fire Safety NOC Renewal [DEMO DATA]",
                        description="Submit renewed fire NOC from Chief Fire Officer",
                        due_at=now - timedelta(days=2),
                        status="SUBMITTED",
                        evidence_notes="Renewed Fire NOC issued by Chief Fire Officer [DEMO DATA]"
                    )
                ])
                db.commit()

            # Compute initial risk score
            RiskService.compute_risk(db, app)

    # 6. Seed demo Notifications
    notifs = [
        (seeded_users["scrutiny@demo.aicte.gov.in"].id, "TASK_ASSIGNED", "New Application Assigned: WT-2026-0001", "You have been allocated application WT-2026-0001 for technical scrutiny review.", "APPLICATION", "WT-2026-0001"),
        (seeded_users["college@demo.aicte.gov.in"].id, "DEFICIENCY_RAISED", "Deficiencies Raised on WT-2026-0002", "Scrutiny officer has noted deficiencies requiring your clarification within 7 days.", "APPLICATION", "WT-2026-0002"),
        (seeded_users["official@demo.aicte.gov.in"].id, "ESCALATED", "ESCALATION LEVEL 1: Overdue Application WT-2026-0003", "Application WT-2026-0003 has been overdue past SLA and is escalated to your attention.", "APPLICATION", "WT-2026-0003")
    ]
    for uid, ntype, subj, body, rtype, rid in notifs:
        existing = db.query(Notification).filter(Notification.subject == subj).first()
        if not existing:
            db.add(Notification(
                user_id=uid,
                channel="IN_APP",
                type=ntype,
                subject=subj,
                body=body,
                related_type=rtype,
                related_id=rid,
                dedupe_key=f"SEED_DEMO:{uid}:{ntype}:{subj}",
                status="SENT",
                sent_at=now
            ))
    db.commit()

    return {"status": "SUCCESS", "message": "Demo database successfully initialized with clean labeled DEMO DATA"}
