from typing import List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.security import decode_access_token

# Swagger /docs Authorize tugmasi bilan ishlashi uchun OAuth2 tokenUrl
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """JWT tokenni tekshiradi va bazadagi joriy foydalanuvchini qaytaradi."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Autentifikatsiyadan o'tilmagan yoki token yaroqsiz",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    return user


def require_roles(allowed_roles: List[str]):
    """Foydalanuvchi roli ruxsat etilgan rollar ro'yxatida borligini tekshiruvchi dependency factory."""

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Ushbu amalni bajarish uchun huquqingiz yetarli emas",
            )
        return current_user

    return role_checker


# Qulay tayyor rollar dependencylari
require_staff_or_admin = require_roles(["staff", "admin"])
require_admin = require_roles(["admin"])
