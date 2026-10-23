from datetime import date, datetime, time, timedelta, timezone
from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.stock_movement import StockMovement

MAX_SAFE_INTEGER = 2_147_483_647  # PostgreSQL 32-bit signed INTEGER chegarasi


def perform_stock_in(
    db: Session,
    product_id: int,
    user_id: int,
    amount: int,
    reason: str,
) -> Tuple[StockMovement, int]:
    """Mahsulotga kirim qilish (SELECT FOR UPDATE va atomik tranzaksiya bilan)."""
    try:
        # 1 & 2. Mahsulot qatorini bloklagan holda tanlab olamiz (SELECT ... FOR UPDATE)
        product = db.query(Product).filter(Product.id == product_id).with_for_update().first()

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID {product_id} bo'lgan mahsulot topilmadi",
            )

        # 3. Integer chegarasidan oshib ketmasligini tekshiramiz
        if product.quantity + amount > MAX_SAFE_INTEGER:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Kirim qilingan miqdor omborning maksimal qoldiq chegarasidan oshib ketadi",
            )

        # 4. Mahsulot qoldig'ini yangilaymiz
        product.quantity += amount

        # 5. Harakatlar tarixiga yangi yozuv qo'shamiz
        movement = StockMovement(
            product_id=product.id,
            performed_by_id=user_id,
            movement_type="incoming",
            amount=amount,
            reason=reason.strip(),
        )
        db.add(movement)

        # 6. Ikkalasini bitta commit bilan saqlaymiz
        db.commit()
        db.refresh(movement)
        return movement, product.quantity

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


def perform_stock_out(
    db: Session,
    product_id: int,
    user_id: int,
    amount: int,
    reason: str,
) -> Tuple[StockMovement, int]:
    """Mahsulotdan chiqim qilish (SELECT FOR UPDATE va atomik tranzaksiya bilan)."""
    try:
        # 1 & 2. Mahsulot qatorini bloklagan holda tanlab olamiz (SELECT ... FOR UPDATE)
        product = db.query(Product).filter(Product.id == product_id).with_for_update().first()

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID {product_id} bo'lgan mahsulot topilmadi",
            )

        # 3. Joriy qoldiq yetarliligini tekshiramiz
        if product.quantity < amount:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Omborda yetarli qoldiq mavjud emas. Joriy qoldiq: {product.quantity}, talab qilingan: {amount}",
            )

        # 4. Qoldiqni kamaytiramiz
        product.quantity -= amount

        # 5. Chiqim tarixini yaratamiz
        movement = StockMovement(
            product_id=product.id,
            performed_by_id=user_id,
            movement_type="outgoing",
            amount=amount,
            reason=reason.strip(),
        )
        db.add(movement)

        # 6. Ikkalasini bitta commit bilan saqlaymiz
        db.commit()
        db.refresh(movement)
        return movement, product.quantity

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


def list_movements(
    db: Session,
    product_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    movement_type: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> Tuple[List[StockMovement], int]:
    """Harakatlar tarixini filtrlash va paginatsiya bilan olish."""
    query = db.query(StockMovement)

    if product_id is not None:
        query = query.filter(StockMovement.product_id == product_id)

    if movement_type is not None:
        if movement_type not in ("incoming", "outgoing"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="movement_type faqat 'incoming' yoki 'outgoing' bo'lishi mumkin",
            )
        query = query.filter(StockMovement.movement_type == movement_type)

    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="date_from sanasi date_to sanasidan katta bo'lishi mumkin emas",
        )

    # Sana filtrlari UTC kunlari bo'yicha to'g'ri hisoblanadi
    if date_from:
        from_datetime = datetime.combine(date_from, time.min).replace(tzinfo=timezone.utc)
        query = query.filter(StockMovement.created_at >= from_datetime)

    if date_to:
        # date_to kunining oxirigacha bo'lgan yozuvlar kirishi uchun: keyingi kun boshlanishidan kichik
        try:
            next_day = date_to + timedelta(days=1)
            to_datetime = datetime.combine(next_day, time.min).replace(tzinfo=timezone.utc)
            query = query.filter(StockMovement.created_at < to_datetime)
        except OverflowError:
            # Sana chegarasi overflow berganda xatolik bo'lmasligi uchun
            to_datetime = datetime.max.replace(tzinfo=timezone.utc)
            query = query.filter(StockMovement.created_at <= to_datetime)

    total = query.count()
    # Eng yangi yozuvlar birinchi, bir xil vaqtli bo'lsa ID bo'yicha barqaror tartiblash
    items = query.order_by(StockMovement.created_at.desc(), StockMovement.id.desc()).offset(offset).limit(limit).all()
    return items, total
