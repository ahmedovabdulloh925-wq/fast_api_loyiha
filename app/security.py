from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.config import settings

# Argon2 xavfsiz parol xeshlagichi
_password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Parolni Argon2 algoritmi orqali xavfsiz xeshlaydi."""
    return _password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Ochiq parolni xesh bilan solishtirib tekshiradi."""
    try:
        return _password_hasher.verify(hashed_password, plain_password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """Foydalanuvchi uchun JWT access token yaratadi."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: Dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }

    encoded_jwt = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """JWT tokenni tekshiradi va uning ma'lumotlarini (payload) qaytaradi."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except jwt.PyJWTError:
        return None
