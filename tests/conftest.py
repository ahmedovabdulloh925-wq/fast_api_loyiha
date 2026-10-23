from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

# Muhim: Test muhitida TEST_DATABASE_URL ni olamiz
from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.security import hash_password

TEST_DB_URL = (
    settings.TEST_DATABASE_URL or "postgresql://warehouse_user:warehouse_password@localhost:5432/warehouse_test_db"
)

# Alohida test engine
test_engine = create_engine(TEST_DB_URL, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Test bazasida Alembic jadvallarini yaratadi."""
    # Jadvallarni test bazasida yaratamiz
    Base.metadata.create_all(bind=test_engine)
    yield
    # Testlar tugagach tozalash
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(autouse=True)
def clean_database():
    """Har bir testdan oldin jadvallarni TRUNCATE qilib tozalaydi."""
    with test_engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE stock_movements, products, users RESTART IDENTITY CASCADE;"))
        conn.commit()


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Testlar uchun DB sessiyasi."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """FastAPI TestClient (test bazasi dependency override bilan)."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def create_test_user(db_session: Session):
    """Test uchun foydalanuvchi yaratish yordamchi funksiyasi."""

    def _create(email: str, password: str, role: str = "user") -> User:
        user = User(
            email=email.strip().lower(),
            password_hash=hash_password(password),
            role=role,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return _create


@pytest.fixture
def admin_token(client: TestClient, create_test_user) -> str:
    """Admin foydalanuvchisi tokeni."""
    create_test_user("admin@example.com", "AdminPass123!", role="admin")
    resp = client.post("/auth/login", data={"username": "admin@example.com", "password": "AdminPass123!"})
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest.fixture
def staff_token(client: TestClient, create_test_user) -> str:
    """Staff foydalanuvchisi tokeni."""
    create_test_user("staff@example.com", "StaffPass123!", role="staff")
    resp = client.post("/auth/login", data={"username": "staff@example.com", "password": "StaffPass123!"})
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest.fixture
def user_token(client: TestClient, create_test_user) -> str:
    """Oddiy user foydalanuvchisi tokeni."""
    create_test_user("user@example.com", "UserPass123!", role="user")
    resp = client.post("/auth/login", data={"username": "user@example.com", "password": "UserPass123!"})
    assert resp.status_code == 200
    return resp.json()["access_token"]
