from typing import Generator, Optional, List
from fastapi import Depends, HTTPException, status, Header, Cookie
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import get_db, utcnow
from app.core.security import decode_token
from app.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

def get_token_from_header_or_cookie(
    auth_header: Optional[str] = Depends(oauth2_scheme),
    access_token_cookie: Optional[str] = Cookie(None, alias="access_token")
) -> Optional[str]:
    if auth_header:
        return auth_header
    if access_token_cookie:
        return access_token_cookie
    return None

def get_current_user(
    token: Optional[str] = Depends(get_token_from_header_or_cookie),
    db: Session = Depends(get_db)
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Authentication required"}
        )
    
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Token expired or invalid"}
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Malformed token payload"}
        )
        
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "USER_NOT_FOUND", "message": "User account no longer exists"}
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "USER_DEACTIVATED", "message": "Account has been deactivated"}
        )
        
    if user.locked_until and user.locked_until > utcnow():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "ACCOUNT_LOCKED", "message": "Account temporarily locked due to failed attempts"}
        )
        
    return user

def require_role(allowed_roles: List[str]):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": f"Role '{current_user.role}' is not authorized for this resource"}
            )
        return current_user
    return role_checker

def verify_institution_access(institution_id: str, current_user: User):
    """Enforces Section 1.3: Institution data isolation"""
    if current_user.role == UserRole.INSTITUTION:
        if current_user.institution_id != institution_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "NOT_FOUND", "message": "Institution resource not found"}
            )
