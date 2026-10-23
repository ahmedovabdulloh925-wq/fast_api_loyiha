from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StockMovementCreate(BaseModel):
    """Kirim yoki chiqim amali uchun so'rov sxemasi."""

    amount: int = Field(gt=0, strict=True)
    reason: str = Field(min_length=1, max_length=1000)

    model_config = ConfigDict(extra="forbid")

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Kirim yoki chiqim sababi bo'sh bo'lishi mumkin emas")
        return v


class StockMovementResponse(BaseModel):
    """Ombor harakati yozuvi sxemasi."""

    id: int
    product_id: int
    performed_by_id: int
    movement_type: str
    amount: int
    reason: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StockOperationResponse(BaseModel):
    """Kirim yoki chiqim amalidan keyin qaytariladigan javob."""

    movement: StockMovementResponse
    updated_quantity: int


class StockMovementListResponse(BaseModel):
    """Harakatlar tarixi ro'yxati va paginatsiya sxemasi."""

    items: List[StockMovementResponse]
    total: int
    limit: int
    offset: int
