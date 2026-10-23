from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ConditionItem(BaseModel):
    title: str
    description: str
    due_days: int = 30

class DecisionCreate(BaseModel):
    decision: str # APPROVE, APPROVED_WITH_CONDITIONS, REJECT
    order_ref: str
    remarks: Optional[str] = None
    conditions: List[ConditionItem] = [] # Auto converted to undertakings if APPROVED_WITH_CONDITIONS

class DecisionResponse(BaseModel):
    id: str
    application_id: str
    decision: str
    decided_by: str
    decided_by_name: Optional[str] = None
    order_ref: Optional[str] = None
    remarks: Optional[str] = None
    decided_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True
