from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.stock_movement import StockMovement
from app.schemas.product import ProductCreate, ProductUpdate


def create_product(db: Session, data: ProductCreate) -> Product:
    """Yangi mahsulot kartasini yaratish (boshlang'ich qoldiq doimo 0)."""
    normalised_sku = data.sku.strip().upper()

    existing = db.query(Product).filter(Product.sku == normalised_sku).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"'{normalised_sku}' SKU bo'yicha mahsulot allaqachon mavjud",
        )

    product = Product(
        name=data.name.strip(),
        sku=normalised_sku,
        description=data.description.strip() if data.description else None,
        quantity=0,
        low_stock_threshold=data.low_stock_threshold,
    )

    try:
        db.add(product)
        db.commit()
        db.refresh(product)
        return product
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"'{normalised_sku}' SKU bo'yicha mahsulot allaqachon mavjud",
        )


def get_product_by_id(db: Session, product_id: int) -> Product:
    """Mahsulotni ID bo'yicha olish (topilmasa 404)."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ID {product_id} bo'lgan mahsulot topilmadi",
        )
    return product


def list_products(
    db: Session,
    search: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> Tuple[List[Product], int]:
    """Mahsulotlar ro'yxatini qidiruv va paginatsiya bilan olish."""
    query = db.query(Product)

    if search and search.strip():
        term = f"%{search.strip().lower()}%"
        query = query.filter(
            or_(
                func.lower(Product.name).like(term),
                func.lower(Product.sku).like(term),
            )
        )

    total = query.count()
    items = query.order_by(Product.id.asc()).offset(offset).limit(limit).all()
    return items, total


def list_out_of_stock(
    db: Session,
    limit: int = 20,
    offset: int = 0,
) -> Tuple[List[Product], int]:
    """Tugagan mahsulotlar (quantity = 0) ro'yxatini olish."""
    query = db.query(Product).filter(Product.quantity == 0)
    total = query.count()
    items = query.order_by(Product.id.asc()).offset(offset).limit(limit).all()
    return items, total


def list_low_stock(
    db: Session,
    limit: int = 20,
    offset: int = 0,
) -> Tuple[List[Product], int]:
    """Qoldig'i kam qolgan mahsulotlar (0 < quantity <= low_stock_threshold) ro'yxati."""
    query = db.query(Product).filter(
        Product.quantity > 0,
        Product.quantity <= Product.low_stock_threshold,
    )
    total = query.count()
    items = query.order_by(Product.id.asc()).offset(offset).limit(limit).all()
    return items, total


def update_product(db: Session, product_id: int, data: ProductUpdate) -> Product:
    """Mahsulot ma'lumotlarini qisman yangilash (PATCH)."""
    product = get_product_by_id(db, product_id)

    # Agar SKU o'zgartirilayotgan bo'lsa, takrorlanmasligini tekshiramiz
    if data.sku is not None:
        normalised_sku = data.sku.strip().upper()
        if normalised_sku != product.sku:
            existing = db.query(Product).filter(Product.sku == normalised_sku).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"'{normalised_sku}' SKU bo'yicha mahsulot allaqachon mavjud",
                )
            product.sku = normalised_sku

    if data.name is not None:
        product.name = data.name.strip()

    if data.description is not None:
        product.description = data.description.strip() if data.description else None

    if data.low_stock_threshold is not None:
        product.low_stock_threshold = data.low_stock_threshold

    try:
        db.commit()
        db.refresh(product)
        return product
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Mahsulot ma'lumotlarini yangilashda ziddiyat yuz berdi",
        )


def delete_product(db: Session, product_id: int) -> None:
    """Mahsulotni o'chirish (agar harakat tarixi bo'lsa 409)."""
    product = get_product_by_id(db, product_id)

    has_movements = db.query(StockMovement).filter(StockMovement.product_id == product_id).first()
    if has_movements:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ushbu mahsulotda ombor harakatlari tarixi mavjud, uni o'chirib bo'lmaydi",
        )

    db.delete(product)
    db.commit()
