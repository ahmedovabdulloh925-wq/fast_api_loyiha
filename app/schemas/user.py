from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserResponse(BaseModel):
    """Foydalanuvchi ma'lumotlarini qaytarish modeli (parol xeshi hech qachon chiqmaydi)."""

    id: int
    email: EmailStr
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
