from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin, require_staff_or_admin
from app.models.user import User
from app.schemas.product import (
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
)
from app.schemas.stock_movement import (
    StockMovementCreate,
    StockOperationResponse,
)
from app.services.product_service import (
    create_product,
    delete_product,
    get_product_by_id,
    list_low_stock,
    list_out_of_stock,
    list_products,
    update_product,
)
from app.services.stock_service import perform_stock_in, perform_stock_out

router = APIRouter(prefix="/products", tags=["Products"])


# -----------------------------------------------------------------------------
# 1. Mahsulot yaratish (Faqat Admin)
# -----------------------------------------------------------------------------
@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yangi mahsulot yaratish (Faqat admin)",
)
def create_new_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
):
    return create_product(db=db, data=data)


# -----------------------------------------------------------------------------
# 2. Mahsulotlar ro'yxati (Staff va Admin)
# -----------------------------------------------------------------------------
@router.get(
    "",
    response_model=ProductListResponse,
    summary="Mahsulotlar ro'yxati (Staff va admin)",
)
def get_products(
    search: Optional[str] = Query(default=None, description="Nomi yoki SKU bo'yicha qidiruv"),
    limit: int = Query(default=20, ge=1, le=100, description="Sahifadagi elementlar soni"),
    offset: int = Query(default=0, ge=0, description="Tashlab ketiladigan elementlar soni"),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_staff_or_admin),
):
    items, total = list_products(db=db, search=search, limit=limit, offset=offset)
    return ProductListResponse(items=items, total=total, limit=limit, offset=offset)


# -----------------------------------------------------------------------------
# 3. Statik yo'llar (Static routes - /{product_id} dan oldin turishi shart!)
# -----------------------------------------------------------------------------
@router.get(
    "/out-of-stock",
    response_model=ProductListResponse,
    summary="Qoldig'i tugagan mahsulotlar (quantity = 0)",
)
def get_out_of_stock_products(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_staff_or_admin),
):
    items, total = list_out_of_stock(db=db, limit=limit, offset=offset)
    return ProductListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/low-stock",
    response_model=ProductListResponse,
    summary="Qoldig'i kam qolgan mahsulotlar (0 < quantity <= low_stock_threshold)",
)
def get_low_stock_products(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_staff_or_admin),
):
    items, total = list_low_stock(db=db, limit=limit, offset=offset)
    return ProductListResponse(items=items, total=total, limit=limit, offset=offset)


# -----------------------------------------------------------------------------
# 4. Dinamik yo'llar (/{product_id})
# -----------------------------------------------------------------------------
@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Mahsulot tafsilotlari (Staff va admin)",
)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_staff_or_admin),
):
    return get_product_by_id(db=db, product_id=product_id)


@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Mahsulotni tahrirlash (Faqat admin, quantity o'zgarmaydi)",
)
def edit_product(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
):
    return update_product(db=db, product_id=product_id, data=data)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Mahsulotni o'chirish (Faqat admin, agar tarixi bo'lmasa)",
)
def remove_product(
    product_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
):
    delete_product(db=db, product_id=product_id)
    return None


# -----------------------------------------------------------------------------
# 5. Kirim va chiqim amallari (Staff va Admin)
# -----------------------------------------------------------------------------
@router.post(
    "/{product_id}/stock-in",
    response_model=StockOperationResponse,
    summary="Mahsulotga kirim qilish (Staff va admin)",
)
def stock_in(
    product_id: int,
    data: StockMovementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_admin),
):
    movement, updated_qty = perform_stock_in(
        db=db,
        product_id=product_id,
        user_id=current_user.id,
        amount=data.amount,
        reason=data.reason,
    )
    return StockOperationResponse(movement=movement, updated_quantity=updated_qty)


@router.post(
    "/{product_id}/stock-out",
    response_model=StockOperationResponse,
    summary="Mahsulotdan chiqim qilish (Staff va admin)",
)
def stock_out(
    product_id: int,
    data: StockMovementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_admin),
):
    movement, updated_qty = perform_stock_out(
        db=db,
        product_id=product_id,
        user_id=current_user.id,
        amount=data.amount,
        reason=data.reason,
    )
    return StockOperationResponse(movement=movement, updated_quantity=updated_qty)
