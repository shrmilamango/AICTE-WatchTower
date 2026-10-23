from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class CommitteeAssignRequest(BaseModel):
    committee_type: str = "SAC" # SAC or SHC
    reviewer_ids: List[str]
    due_days: int = 7

class CommitteeReviewSubmit(BaseModel):
    recommendation: str # RECOMMENDED, NOT_RECOMMENDED, CONDITIONAL
    remarks: str

class CommitteeReviewResponse(BaseModel):
    id: str
    application_id: str
    committee_type: str
    reviewer_id: str
    reviewer_name: Optional[str] = None
    status: str
    recommendation: Optional[str] = None
    remarks: Optional[str] = None
    due_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
