from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.auth import RegisterRequest
from app.security import hash_password, verify_password


def register_user(db: Session, request: RegisterRequest) -> User:
    """Yangi oddiy foydalanuvchini ro'yxatdan o'tkazish (doim 'user' roli bilan)."""
    normalised_email = request.email.strip().lower()

    # Bazada bunday email bor-yo'qligini tekshiramiz
    existing_user = db.query(User).filter(User.email == normalised_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ushbu email manzili bilan foydalanuvchi allaqachon mavjud",
        )

    new_user = User(
        email=normalised_email,
        password_hash=hash_password(request.password),
        role="user",
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ushbu email manzili bilan foydalanuvchi allaqachon mavjud",
        )


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Email va parolni tekshirib foydalanuvchini autentifikatsiya qilish."""
    normalised_email = email.strip().lower()
    user = db.query(User).filter(User.email == normalised_email).first()
    if not user:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user
