from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import CheckConstraint, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.stock_movement import StockMovement


class Product(Base):
    """Ombordagi mahsulot modeli."""

    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="check_product_quantity_non_negative"),
        CheckConstraint("low_stock_threshold >= 0", name="check_product_threshold_non_negative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    sku: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    low_stock_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Mahsulotning ombor harakatlari tarixi
    movements: Mapped[List["StockMovement"]] = relationship(
        "StockMovement",
        back_populates="product",
        passive_deletes=False,
    )
