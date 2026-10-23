from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    """Foydalanuvchi ro'yxatdan o'tishi uchun so'rov modeli."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    model_config = ConfigDict(extra="forbid")

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("password")
    @classmethod
    def validate_password_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Parol faqat bo'sh joylardan iborat bo'lishi mumkin emas")
        return v


class TokenResponse(BaseModel):
    """Muvaffaqiyatli kirishda qaytariladigan JWT token modeli."""

    access_token: str
    token_type: str = "bearer"
