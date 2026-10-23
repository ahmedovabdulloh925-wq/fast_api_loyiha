from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.security import create_access_token


def test_register_success(client: TestClient, db_session: Session):
    """Muvaffaqiyatli ro'yxatdan o'tish tekshiruvi (201)."""
    response = client.post(
        "/auth/register",
        json={"email": "abdulloh@example.com", "password": "StrongPassword123!"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "abdulloh@example.com"
    assert data["role"] == "user"
    assert "id" in data
    # Xavfsizlik: javobda parol yoki hash bo'lmasligi kerak
    assert "password" not in data
    assert "password_hash" not in data

    # Bazada saqlanganligini tekshiramiz
    user = db_session.query(User).filter(User.email == "abdulloh@example.com").first()
    assert user is not None
    # Parol ochiq matnda saqlanmagan, Argon2 xeshi ko'rinishida
    assert user.password_hash != "StrongPassword123!"
    assert user.password_hash.startswith("$argon2")


def test_register_duplicate_email_case_normalisation(client: TestClient):
    """Katta-kichik harflar bilan bir xil email ro'yxatdan o'tganda 409 qaytarishi."""
    resp1 = client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "Password123!"},
    )
    assert resp1.status_code == 201

    resp2 = client.post(
        "/auth/register",
        json={"email": "  TEST@EXAMPLE.COM  ", "password": "Password123!"},
    )
    assert resp2.status_code == 409
    assert "allaqachon mavjud" in resp2.json()["detail"]


def test_register_rejects_extra_fields(client: TestClient):
    """Ro'yxatdan o'tishda 'role' kabi qo'shimcha maydonlar yuborilsa 422 berishi."""
    response = client.post(
        "/auth/register",
        json={
            "email": "hacker@example.com",
            "password": "Password123!",
            "role": "admin",  # Taqiqlangan ortiqcha maydon
        },
    )
    assert response.status_code == 422


def test_register_short_password(client: TestClient):
    """8 belgidan kam bo'lgan parol rad etilishi kerak (422)."""
    response = client.post(
        "/auth/register",
        json={"email": "short@example.com", "password": "123"},
    )
    assert response.status_code == 422


def test_login_success(client: TestClient, create_test_user):
    """To'g'ri login bilan JWT token olish."""
    create_test_user("login@example.com", "SecretPass123!", role="user")

    # OAuth2 form formatida so'rov
    response = client.post(
        "/auth/login",
        data={"username": "login@example.com", "password": "SecretPass123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials_generic_message(client: TestClient, create_test_user):
    """Noto'g'ri email yoki parolda email mavjudligini oshkor qilmaydigan umumiy 401 xabar."""
    create_test_user("exist@example.com", "SecretPass123!", role="user")

    # Noto'g'ri parol
    resp1 = client.post(
        "/auth/login",
        data={"username": "exist@example.com", "password": "WrongPassword"},
    )
    assert resp1.status_code == 401
    assert resp1.json()["detail"] == "Email yoki parol noto'g'ri"

    # Mavjud bo'lmagan email
    resp2 = client.post(
        "/auth/login",
        data={"username": "notexist@example.com", "password": "SecretPass123!"},
    )
    assert resp2.status_code == 401
    assert resp2.json()["detail"] == "Email yoki parol noto'g'ri"


def test_users_me_success(client: TestClient, user_token: str):
    """GET /users/me orqali joriy foydalanuvchini olish."""
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "user@example.com"
    assert data["role"] == "user"
    assert "password_hash" not in data


def test_users_me_invalid_token(client: TestClient):
    """Noto'g'ri yoki buzilgan token bilan 401 va WWW-Authenticate qaytishi."""
    response = client.get(
        "/users/me",
        headers={"Authorization": "Bearer this-is-invalid-token"},
    )
    assert response.status_code == 401
    assert response.headers.get("www-authenticate") == "Bearer"


def test_users_me_expired_token(client: TestClient, create_test_user):
    """Muddati o'tgan token rad etilishi kerak (401)."""
    user = create_test_user("expired@example.com", "Password123!", role="user")
    # -10 daqiqa oldin o'tib ketgan token yaratamiz
    expired_token = create_access_token(
        subject=str(user.id),
        expires_delta=timedelta(minutes=-10),
    )

    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
    assert response.headers.get("www-authenticate") == "Bearer"
