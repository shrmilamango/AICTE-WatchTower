from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class DeficiencyItemCreate(BaseModel):
    item: str
    description: str
    due_days: int = 7

class ScrutinyReviewCreate(BaseModel):
    outcome: str # PASS or DEFICIENT
    remarks: Optional[str] = None
    deficiencies: List[DeficiencyItemCreate] = []

class DeficiencyResponse(BaseModel):
    id: str
    review_id: str
    item: str
    description: str
    status: str
    due_at: datetime
    response_text: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    is_overdue: bool = False

    class Config:
        from_attributes = True

class DeficiencyRespondItem(BaseModel):
    deficiency_id: str
    response_text: str

class DeficienciesRespondRequest(BaseModel):
    responses: List[DeficiencyRespondItem]
