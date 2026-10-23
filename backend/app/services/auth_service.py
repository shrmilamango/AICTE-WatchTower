from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import utcnow
from app.core.security import verify_password, hash_password, create_access_token, create_refresh_token
from app.core.audit import log_audit
from app.models.user import User

LOCKOUT_ATTEMPTS = 5
LOCKOUT_MINUTES = 10

class AuthService:
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str, ip_address: Optional[str] = None) -> Tuple[User, str, str]:
        user = db.query(User).filter(User.email == email.lower().strip()).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_CREDENTIALS", "message": "Invalid email or password"}
            )
            
        now = utcnow()
        if user.locked_until and user.locked_until > now:
            minutes_left = int((user.locked_until - now).total_seconds() / 60) + 1
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "ACCOUNT_LOCKED", "message": f"Account is locked. Try again in {minutes_left} minutes."}
            )
            
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "USER_DEACTIVATED", "message": "Account has been deactivated"}
            )
            
        if not verify_password(password, user.password_hash):
            user.failed_attempts += 1
            if user.failed_attempts >= LOCKOUT_ATTEMPTS:
                user.locked_until = now + timedelta(minutes=LOCKOUT_MINUTES)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_CREDENTIALS", "message": "Invalid email or password"}
            )
            
        # Reset failed attempts on success
        user.failed_attempts = 0
        user.locked_until = None
        user.last_login = now
        db.commit()
        
        token_data = {"sub": user.id, "email": user.email, "role": user.role}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        log_audit(
            db=db,
            action="LOGIN_SUCCESS",
            entity_type="USER",
            entity_id=user.id,
            actor_id=user.id,
            ip_address=ip_address
        )
        
        return user, access_token, refresh_token

    @staticmethod
    def change_password(db: Session, user: User, old_password: str, new_password: str) -> bool:
        if not verify_password(old_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_OLD_PASSWORD", "message": "Current password does not match"}
            )
            
        if len(new_password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "WEAK_PASSWORD", "message": "Password must be at least 8 characters"}
            )
            
        user.password_hash = hash_password(new_password)
        db.commit()
        
        log_audit(
            db=db,
            action="CHANGE_PASSWORD",
            entity_type="USER",
            entity_id=user.id,
            actor_id=user.id
        )
        return True

    @staticmethod
    def deactivate_user(db: Session, user_id: str, admin_user: User) -> User:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail={"code": "USER_NOT_FOUND", "message": "User not found"})
        
        before = {"is_active": user.is_active}
        user.is_active = False
        db.commit()
        
        log_audit(
            db=db,
            action="DEACTIVATE_USER",
            entity_type="USER",
            entity_id=user.id,
            actor_id=admin_user.id,
            before_state=before,
            after_state={"is_active": False}
        )
        return user
