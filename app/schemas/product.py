from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductCreate(BaseModel):
    """Yangi mahsulot yaratish sxemasi."""

    name: str = Field(min_length=1, max_length=200)
    sku: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=2000)
    low_stock_threshold: int = Field(default=0, ge=0, strict=True)

    model_config = ConfigDict(extra="forbid")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Mahsulot nomi faqat bo'shliqlardan iborat bo'lishi mumkin emas")
        return v

    @field_validator("sku")
    @classmethod
    def validate_sku(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("SKU faqat bo'shliqlardan iborat bo'lishi mumkin emas")
        return v


class ProductUpdate(BaseModel):
    """Mahsulotni tahrirlash sxemasi (quantity tahrirlanmaydi)."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    sku: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=2000)
    low_stock_threshold: Optional[int] = Field(default=None, ge=0, strict=True)

    model_config = ConfigDict(extra="forbid")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Mahsulot nomi bo'sh bo'lishi mumkin emas")
        return v

    @field_validator("sku")
    @classmethod
    def validate_sku(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip().upper()
            if not v:
                raise ValueError("SKU bo'sh bo'lishi mumkin emas")
        return v


class ProductResponse(BaseModel):
    """Mahsulot ma'lumotlarini qaytarish sxemasi."""

    id: int
    name: str
    sku: str
    description: Optional[str] = None
    quantity: int
    low_stock_threshold: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductListResponse(BaseModel):
    """Mahsulotlar ro'yxati va paginatsiya sxemasi."""

    items: List[ProductResponse]
    total: int
    limit: int
    offset: int
