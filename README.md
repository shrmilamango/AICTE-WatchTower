# AICTE WATCHTOWER 🛡️
> **Automation and Monitoring of AICTE Approval Workflows**  
> Complete build specification implemented according to *AICTE WATCHTOWER*.

---

## 🌟 Overview & Core Value
AICTE WATCHTOWER is a single unified platform that:
- **Routes each technical approval application** through configurable Approval Process Handbook (APH) stages with explicit owner and SLA deadlines at every step.
- **Eliminates stalled cases**: Tracks where each pending item is stuck, how long it has been there, and with whom.
- **Automates scrutiny, deficiencies, resubmission**, Expert Visit Committee (EVC) scheduling, SAC/SHC review, and conditional approval decisions.
- **Guarantees compliance oversight**: Approval conditions automatically become tracked undertakings; documents with validity (such as registered land lease deeds and fire safety NOCs) are monitored perpetually with automated renewal warnings.
- **Proactive 2-level escalation**: Overdue deadlines trigger instant in-app alerts and escalate hierarchically without manual chasing.
- **Explainable 0–100 Delay-Risk Matrix**: Real-time rule-based risk factors with clear, human-readable explanations.
- **Tamper-resistant append-only audit trail**: Tracks every login, transition, decision, upload, download, and configuration change.

---

## 🏛️ Architecture & Tech Stack

| Layer | Technology | Role |
|---|---|---|
| **Frontend** | React 19 + Vite, Vanilla CSS Design System, Recharts, Lucide Icons | Role-based portals, executive dashboards, interactive timelines |
| **Backend** | Python 3.14 + FastAPI, Pydantic v2, SQLAlchemy 2.0 | High-performance REST APIs, state machine engine, RBAC, data isolation |
| **Database** | SQLite (zero-config local dev & demo) / PostgreSQL 15 | Append-only audit logs, relational entities, workflow state |
| **Background Engine** | In-Process Scheduler & Celery/Redis compatible | Hourly SLA monitoring, overdue marking, 2-tier escalation engine |
| **Testing** | pytest, httpx, in-memory SQLite with StaticPool | 100% automated test coverage of all "Done when" requirements |

---

## 🚀 Quick Start (Local Run)

### 1. Backend Setup & Start
```powershell
cd d:\aicte-watchtower\backend
# Create virtual environment (already set up)
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
*Backend Swagger Docs:* [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)  
*Health Check:* [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

### 2. Frontend Setup & Start
```powershell
cd d:\aicte-watchtower\frontend
$env:PATH = "C:\Program Files\nodejs;" + $env:PATH
npm run dev -- --host 127.0.0.1 --port 5173
```
*Frontend Web Portal:* [http://127.0.0.1:5173](http://127.0.0.1:5173)

---

## 🔑 Demo Login Credentials
All demo accounts use password: `Password@123` (or use the **1-click Role Selector** on the login screen):

| Role | Email | Description |
|---|---|---|
| **INSTITUTION** | `college@demo.aicte.gov.in` | Delhi Institute of Technology [DEMO DATA] |
| **SCRUTINY_OFFICER** | `scrutiny@demo.aicte.gov.in` | Dr. A. K. Sharma (North Region Scrutiny Officer) |
| **EVC_COORDINATOR** | `evc@demo.aicte.gov.in` | Er. Rajesh Verma (Regional EVC Coordinator) |
| **COMMITTEE_MEMBER** | `committee@demo.aicte.gov.in` | Prof. M. S. Swaminathan (SAC/SHC Member) |
| **AUTHORISED_OFFICIAL** | `official@demo.aicte.gov.in` | Dr. Rekha Gupta (Regional Officer & Authorised Official) |
| **ADMIN** | `admin@demo.aicte.gov.in` | System Administrator (Ruleset & Template Editor) |
| **AUDITOR** | `auditor@demo.aicte.gov.in` | Chief Compliance Auditor (Read-only Oversight) |

---

## 🧪 Automated Testing
Run the complete automated test suite verifying all "Done when" requirements:
```powershell
cd d:\aicte-watchtower\backend
$env:PYTHONPATH = "d:\aicte-watchtower\backend"
.\venv\Scripts\pytest.exe -v app/tests/test_watchtower.py
```
*All 12 module tests pass with 100% success rate.*

---

## 📋 5-Minute Demo Checklist (Section 6.5)
1. **Login as Institution** (`college@demo.aicte.gov.in`), create a draft application, attach documents, and submit to generate official number `WT-2026-0001`.
2. **Login as Scrutiny Officer** (`scrutiny@demo.aicte.gov.in`), open assigned case, select `DEFICIENT`, itemize deficiencies with SLA due days, and return to college.
3. **Login as Institution**, respond to each deficiency item with corrective remarks and resubmit back to the same scrutiny officer.
4. **Schedule EVC Visit** as EVC Coordinator (`evc@demo.aicte.gov.in`), appoint committee chairman and experts, and set inspection date.
5. **Presentation Trigger**: Click the header `"Run Scheduler Now"` button to demonstrate instant SLA checking, overdue detection, and Level 1 / Level 2 hierarchical escalation.
6. **Record Conditional Approval**: As Authorised Official (`official@demo.aicte.gov.in`), record decision `APPROVED_WITH_CONDITIONS`, which automatically generates mandatory undertakings.
7. **View Dashboard & Risk Matrix**: Inspect live counts, pendency charts by stage/region/age, and the 0–100 explainable risk list with full factor attribution.
8. **Inspect Tamper Audit Trail**: Retrieve full append-only audit history for any application with before/after state diffs and CSV export.
>>>>>>> 0d5bcf0 (feat: complete implementation of AICTE Watchtower approval automation and oversight platform)
