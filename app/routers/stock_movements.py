from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_staff_or_admin
from app.models.user import User
from app.schemas.stock_movement import StockMovementListResponse
from app.services.stock_service import list_movements

router = APIRouter(prefix="/stock-movements", tags=["Stock Movements"])


@router.get(
    "",
    response_model=StockMovementListResponse,
    summary="Ombor harakatlari tarixi (Staff va admin)",
    description="Mahsulot, sana oralig'i va kirim/chiqim yo'nalishi bo'yicha filtrlash imkoniyati bilan.",
)
def get_stock_movements(
    product_id: Optional[int] = Query(default=None, description="Mahsulot ID bo'yicha filter"),
    date_from: Optional[date] = Query(default=None, description="Boshlang'ich sana (YYYY-MM-DD, UTC)"),
    date_to: Optional[date] = Query(default=None, description="Tugash sanasi (YYYY-MM-DD, UTC)"),
    movement_type: Optional[str] = Query(
        default=None,
        description="Harakat turi ('incoming' yoki 'outgoing')",
    ),
    limit: int = Query(default=20, ge=1, le=100, description="Sahifadagi yozuvlar soni"),
    offset: int = Query(default=0, ge=0, description="Tashlab ketiladigan yozuvlar soni"),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_staff_or_admin),
):
    items, total = list_movements(
        db=db,
        product_id=product_id,
        date_from=date_from,
        date_to=date_to,
        movement_type=movement_type,
        limit=limit,
        offset=offset,
    )
    return StockMovementListResponse(items=items, total=total, limit=limit, offset=offset)
