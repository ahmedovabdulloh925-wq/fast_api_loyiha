from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers.auth import router as auth_router
from app.routers.products import router as products_router
from app.routers.stock_movements import router as stock_movements_router
from app.routers.users import router as users_router

app = FastAPI(
    title="Warehouse Management API",
    description=(
        "Ombordagi mahsulotlar va ularning kirim-chiqim harakatlarini "
        "boshqarish uchun sodda va ishonchli REST API tizimi."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Routerlarni ulash
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(products_router)
app.include_router(stock_movements_router)


@app.get(
    "/health",
    tags=["Health"],
    summary="Tizim va ma'lumotlar bazasi holatini tekshirish",
    description="Autentifikatsiyasiz ishlaydi. Ma'lumotlar bazasiga yengil SELECT 1 so'rovi yuboradi.",
)
def health_check(db: Session = Depends(get_db)):
    """Ilova va PostgreSQL bazasi salomatligini tekshirish."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ma'lumotlar bazasiga ulanib bo'lmadi",
        )
@app.get(
    "/",
    tags=["Root"],
    summary="Bosh sahifa",
)
def read_root():
    """API ishlayotgani haqida asosiy ma'lumot va Swagger'ga o'tish havolasi."""
    return {
        "app": "Warehouse Management API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "active"
    }