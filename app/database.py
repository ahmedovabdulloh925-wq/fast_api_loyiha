from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import settings

# Synchronous PostgreSQL engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

# Har bir HTTP so'rov uchun alohida Session yaratish fabrikasi
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Barcha SQLAlchemy modellarining ota klassi
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI endpointlari uchun ma'lumotlar bazasi sessiyasini taqdim etuvchi dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
