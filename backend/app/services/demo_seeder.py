from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.database import utcnow
from app.core.security import hash_password
from app.core.audit import log_audit
from app.models.user import User, UserRole
from app.models.institution import Institution
from app.models.workflow import WorkflowTemplate, WorkflowStage, Application, ApplicationStageHistory, Task
from app.models.scrutiny import ScrutinyReview, Deficiency
from app.models.evc import EvcVisit
from app.models.committee import CommitteeReview
from app.models.decision import Decision
from app.models.compliance import Undertaking, Document
from app.models.alert import Notification, ReminderRule, EscalationRule
from app.models.risk import RiskScore
from app.models.config import ConfigRule
from app.workflow.engine import WorkflowEngine
from app.services.config_service import ConfigService
from app.services.risk_service import RiskService

DEFAULT_PASSWORD = "Password@123"

def seed_demo_database(db: Session) -> dict:
    now = utcnow()

    # 1. Initialize configs and template
    ConfigService.init_default_configs(db)
    template = WorkflowEngine.get_active_template(db)

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
            EscalationRule(target_type="TASK", level=1, after_overdue_days=2, escalate_to_role=UserRole.AUTHORISED_OFFICIAL, active=True),
            EscalationRule(target_type="TASK", level=2, after_overdue_days=5, escalate_to_role=UserRole.ADMIN, active=True)
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
            contact_name="Dr. Ramanathan Iyer",
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
            contact_name="Dr. Shailesh Kulkarni",
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
        ("official@demo.aicte.gov.in", "Dr. Rekha Gupta (Authorised Official)", UserRole.AUTHORISED_OFFICIAL, None, "NORTH"),
        ("scrutiny@demo.aicte.gov.in", "Dr. A. K. Sharma (Scrutiny Officer)", UserRole.SCRUTINY_OFFICER, None, "NORTH"),
        ("scrutiny2@demo.aicte.gov.in", "Dr. Sunita Rao (Scrutiny Officer)", UserRole.SCRUTINY_OFFICER, None, "WEST"),
        ("evc@demo.aicte.gov.in", "Er. Rajesh Verma (EVC Coordinator)", UserRole.EVC_COORDINATOR, None, "NORTH"),
        ("committee@demo.aicte.gov.in", "Prof. M. S. Swaminathan (SAC Member)", UserRole.COMMITTEE_MEMBER, None, "NORTH"),
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
        seeded_users[email] = u

    # 5. Seed Applications at various realistic pipeline stages
    apps_data = [
        ("WT-2026-0001", inst1.id, "Engineering & Technology", "UNDER_SCRUTINY", seeded_users["scrutiny@demo.aicte.gov.in"].id),
        ("WT-2026-0002", inst1.id, "Management", "DEFICIENCY_RAISED", seeded_users["college@demo.aicte.gov.in"].id),
        ("WT-2026-0003", inst1.id, "Pharmacy", "EVC_REQUIRED", seeded_users["evc@demo.aicte.gov.in"].id),
        ("WT-2026-0004", inst2.id, "Engineering & Technology", "EVC_SCHEDULED", seeded_users["evc@demo.aicte.gov.in"].id),
        ("WT-2026-0005", inst2.id, "Computer Applications (MCA)", "COMMITTEE_REVIEW", seeded_users["committee@demo.aicte.gov.in"].id),
        ("WT-2026-0006", inst1.id, "Architecture & Planning", "APPROVED_WITH_CONDITIONS", seeded_users["official@demo.aicte.gov.in"].id)
    ]

    for app_no, i_id, prog, st, owner_id in apps_data:
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
                submitted_at=now - timedelta(days=12)
            )
            db.add(app)
            db.commit()
            db.refresh(app)

            # Stage history
            hist = ApplicationStageHistory(
                application_id=app.id,
                stage_key=st,
                entered_at=now - timedelta(days=5),
                due_at=now + timedelta(days=2),
                owner_id=owner_id
            )
            db.add(hist)

            # Stage task
            is_overdue = (app_no == "WT-2026-0003") # make WT-0003 overdue to demonstrate risk & escalation
            task = Task(
                application_id=app.id,
                type=st,
                assigned_to=owner_id,
                role=UserRole.SCRUTINY_OFFICER if "SCRUTINY" in st else UserRole.EVC_COORDINATOR if "EVC" in st else UserRole.AUTHORISED_OFFICIAL,
                due_at=now - timedelta(days=3) if is_overdue else now + timedelta(days=4),
                status="OVERDUE" if is_overdue else "OPEN",
                escalation_level=1 if is_overdue else 0
            )
            db.add(task)
            db.commit()

            # Add stage-specific auxiliary records
            if st == "DEFICIENCY_RAISED":
                rev = ScrutinyReview(
                    application_id=app.id,
                    reviewer_id=seeded_users["scrutiny@demo.aicte.gov.in"].id,
                    round_no=1,
                    outcome="DEFICIENT",
                    remarks="Faculty cadre ratio does not meet 1:15 norm; Land registration deed not attested [DEMO DATA]"
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
                        due_at=now + timedelta(days=5)
                    ),
                    Deficiency(
                        review_id=rev.id,
                        item="Fire Safety Certificate",
                        description="Municipal Fire Safety NOC submitted is past validity date [DEMO DATA]",
                        status="OPEN",
                        due_at=now + timedelta(days=5)
                    )
                ])
                db.commit()

            elif st == "EVC_REQUIRED":
                # Unscheduled visit past target date for demonstration
                visit = EvcVisit(
                    application_id=app.id,
                    status="REQUIRED",
                    target_date=now - timedelta(days=2), # overdue!
                    coordinator_id=seeded_users["evc@demo.aicte.gov.in"].id,
                    remarks="Awaiting constitution of expert visit team [DEMO DATA]"
                )
                db.add(visit)
                db.commit()

            elif st == "EVC_SCHEDULED":
                visit = EvcVisit(
                    application_id=app.id,
                    status="SCHEDULED",
                    target_date=now + timedelta(days=10),
                    scheduled_date=now + timedelta(days=6),
                    members=[
                        {"name": "Prof. H. C. Verma", "affiliation": "IIT Kanpur", "role": "Chairman"},
                        {"name": "Dr. Sunita Deshmukh", "affiliation": "COEP Pune", "role": "Member"}
                    ],
                    coordinator_id=seeded_users["evc@demo.aicte.gov.in"].id,
                    remarks="Physical inspection of laboratories, computing infrastructure and workshops [DEMO DATA]"
                )
                db.add(visit)
                db.commit()

            elif st == "COMMITTEE_REVIEW":
                crev = CommitteeReview(
                    application_id=app.id,
                    committee_type="SAC",
                    reviewer_id=seeded_users["committee@demo.aicte.gov.in"].id,
                    status="PENDING",
                    due_at=now + timedelta(days=4)
                )
                db.add(crev)
                db.commit()

            elif st == "APPROVED_WITH_CONDITIONS":
                dec = Decision(
                    application_id=app.id,
                    decision="APPROVED_WITH_CONDITIONS",
                    decided_by=seeded_users["official@demo.aicte.gov.in"].id,
                    order_ref="AICTE/NWRO/2026/COND-882",
                    remarks="Approval granted subject to submission of updated registered lease deed and fire certificate within 30 days [DEMO DATA]",
                    decided_at=now - timedelta(days=10)
                )
                db.add(dec)
                db.commit()

                # Seed 2 undertakings
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
                        due_at=now - timedelta(days=2), # Overdue undertaking!
                        status="OVERDUE"
                    )
                ])
                db.commit()

            # Seed documents with validity for institution
            if app_no == "WT-2026-0001":
                db.add_all([
                    Document(
                        institution_id=i_id,
                        application_id=app.id,
                        doc_type="LAND_LEASE",
                        file_name="Lease_Deed_Campus_2026.pdf",
                        storage_key="demo_lease_deed.pdf",
                        mime="application/pdf",
                        size=2450000,
                        uploaded_by=seeded_users["college@demo.aicte.gov.in"].id,
                        version_no=1,
                        valid_from=now - timedelta(days=365),
                        valid_until=now + timedelta(days=14), # EXPIRING in 14 days!
                        status="EXPIRING"
                    ),
                    Document(
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

    return {"status": "SUCCESS", "message": "Demo database successfully initialized with labelled DEMO DATA"}
