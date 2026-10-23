import uuid
from datetime import datetime, timezone
from typing import Generator
from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

def get_engine_kwargs(database_url: str):
    if database_url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {}

engine = create_engine(settings.DATABASE_URL, **get_engine_kwargs(settings.DATABASE_URL))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class BaseModel(Base):
    __abstract__ = True
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
