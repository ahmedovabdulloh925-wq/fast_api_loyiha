from app.routers.auth import router as auth_router
from app.routers.products import router as products_router
from app.routers.stock_movements import router as stock_movements_router
from app.routers.users import router as users_router

__all__ = ["auth_router", "users_router", "products_router", "stock_movements_router"]
