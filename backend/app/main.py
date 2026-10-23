import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.database import engine, SessionLocal, Base
import app.models # Register all models with Base
from app.services.config_service import ConfigService
from app.workflow.engine import WorkflowEngine
from app.services.demo_seeder import seed_demo_database

# Routers
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.institutions import router as institutions_router
from app.api.v1.applications import router as applications_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.evc import router as evc_router
from app.api.v1.committee import router as committee_router
from app.api.v1.compliance import router as compliance_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.risk import router as risk_router
from app.api.v1.admin import router as admin_router
from app.api.v1.audit import router as audit_router
from app.api.v1.reports import router as reports_router
from app.api.v1.health import router as health_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables and seed default data
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        ConfigService.init_default_configs(db)
        WorkflowEngine.get_active_template(db)
        seed_demo_database(db)
    finally:
        db.close()
    yield

app = FastAPI(
    title=settings.APP_NAME,
    description="AICTE WATCHTOWER — Automation and Monitoring of AICTE Approval Workflows",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rule 2.4: Standard error response shape
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": detail}
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "HTTP_ERROR", "message": str(detail), "details": {}}}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Validation error in request payload",
                "details": errors
            }
        }
    )

# Include Routers under /api/v1
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(institutions_router, prefix="/api/v1")
app.include_router(applications_router, prefix="/api/v1")
app.include_router(tasks_router, prefix="/api/v1")
app.include_router(evc_router, prefix="/api/v1")
app.include_router(committee_router, prefix="/api/v1")
app.include_router(compliance_router, prefix="/api/v1")
app.include_router(alerts_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(risk_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(audit_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")

@app.get("/")
def root():
    return {
        "name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "docs_url": "/docs",
        "api_v1_prefix": "/api/v1"
    }
