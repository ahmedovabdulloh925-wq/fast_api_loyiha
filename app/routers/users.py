from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Joriy foydalanuvchi ma'lumotlari",
    description="Bearer token orqali tizimga kirgan foydalanuvchining o'z ma'lumotlarini qaytaradi.",
)
def get_me(current_user: User = Depends(get_current_user)):
    """Joriy foydalanuvchi profilini qaytarish."""
    return current_user
