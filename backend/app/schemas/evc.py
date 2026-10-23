from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

class EvcMember(BaseModel):
    name: str
    affiliation: str
    role: str # Expert, Chairman, Member

class EvcScheduleRequest(BaseModel):
    scheduled_date: datetime
    members: List[EvcMember] = []
    remarks: Optional[str] = None

class EvcCompleteRequest(BaseModel):
    outcome: str # COMPLETED, SATISFACTORY, UNSATISFACTORY
    report_document_id: Optional[str] = None
    remarks: str

class EvcResponse(BaseModel):
    id: str
    application_id: str
    app_no: Optional[str] = None
    institution_name: Optional[str] = None
    status: str
    target_date: Optional[datetime] = None
    scheduled_date: Optional[datetime] = None
    members: List[Any] = []
    coordinator_id: Optional[str] = None
    coordinator_name: Optional[str] = None
    report_document_id: Optional[str] = None
    remarks: Optional[str] = None
    created_at: datetime
    is_unscheduled_alert: bool = False

    class Config:
        from_attributes = True
