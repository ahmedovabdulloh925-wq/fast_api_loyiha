from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import RegisterRequest, TokenResponse
from app.schemas.user import UserResponse
from app.security import create_access_token
from app.services.auth_service import authenticate_user, register_user

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yangi foydalanuvchini ro'yxatdan o'tkazish",
    description="Ochiq ro'yxatdan o'tish orqali faqat oddiy 'user' roli beriladi. Qo'shimcha maydonlar rad etiladi.",
)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Yangi foydalanuvchi yaratish."""
    user = register_user(db=db, request=request)
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Tizimga kirish va JWT token olish",
    description="OAuth2 standartidagi form. Swagger Authorize ishlashi uchun 'username' maydoniga email kiriting.",
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Foydalanuvchi emaili va parolini tekshirib, JWT token qaytaradi."""
    user = authenticate_user(db=db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email yoki parol noto'g'ri",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=access_token, token_type="bearer")
