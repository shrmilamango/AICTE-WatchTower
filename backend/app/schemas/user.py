from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Any
from datetime import datetime

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserResponse"

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str
    institution_id: Optional[str] = None
    region: Optional[str] = None
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    institution_id: Optional[str] = None
    region: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

TokenResponse.model_rebuild()
