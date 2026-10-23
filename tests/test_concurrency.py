import concurrent.futures
import threading

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.models.product import Product
from app.models.stock_movement import StockMovement
from tests.conftest import TestingSessionLocal


@pytest.fixture
def concurrency_client(create_test_user):
    """Parallel so'rovlar uchun har bir requestga yangi PostgreSQL sessiyasini beruvchi client."""

    def _get_fresh_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _get_fresh_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_concurrent_stock_out_prevents_negative_balance(concurrency_client: TestClient, create_test_user):
    """
    Qoldiq 10 bo'lganda bir vaqtda ikkita 7 birlik chiqim:
    - Faqat bittasi muvaffaqiyatli (200)
    - Ikkinchisi rad etiladi (409)
    - Yakuniy qoldiq 3 bo'lib qoladi
    - Rad etilgan chiqim tarixga kirmaydi
    """
    # 1. Foydalanuvchilar va mahsulotni tayyorlaymiz
    create_test_user("admin_conc@example.com", "Password123!", role="admin")
    login_resp = concurrency_client.post(
        "/auth/login",
        data={"username": "admin_conc@example.com", "password": "Password123!"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Mahsulot yaratamiz
    p_resp = concurrency_client.post(
        "/products",
        json={"name": "Rare Laptop", "sku": "LAP-01"},
        headers=headers,
    )
    prod_id = p_resp.json()["id"]

    # 10 birlik kirim qilamiz
    concurrency_client.post(
        f"/products/{prod_id}/stock-in",
        json={"amount": 10, "reason": "Boshlang'ich partiya"},
        headers=headers,
    )

    # 2. Concurrency sozlash: ikkita so'rovni bir vaqtda start berish uchun Barrier
    barrier = threading.Barrier(2)
    results = []

    def perform_out():
        # Barrier orqali ikkala oqim ham tayyor bo'lishini kutamiz va bir vaqtda uramiz
        barrier.wait(timeout=5)
        # Yangi client sessiyasi bilan so'rov yuboramiz
        resp = concurrency_client.post(
            f"/products/{prod_id}/stock-out",
            json={"amount": 7, "reason": "Parallel sotuv"},
            headers=headers,
        )
        return resp.status_code, resp.json()

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(perform_out)
        f2 = executor.submit(perform_out)
        results = [f1.result(timeout=10), f2.result(timeout=10)]

    status_codes = [r[0] for r in results]

    # Bittasi 200, ikkinchisi 409 bo'lishi shart!
    assert 200 in status_codes, f"Kutilgan 200 topilmadi: {status_codes}"
    assert 409 in status_codes, f"Kutilgan 409 topilmadi: {status_codes}"

    # 3. Yakuniy qoldiqni bazadan to'g'ridan-to'g'ri tekshiramiz
    db = TestingSessionLocal()
    try:
        product = db.query(Product).filter(Product.id == prod_id).first()
        assert product.quantity == 3, f"Kutilgan qoldiq 3, lekin {product.quantity} chiqdi!"

        # Tarixda faqat 1 ta kirim va 1 ta muvaffaqiyatli chiqim bo'lishi kerak (jami 2 ta)
        movements = db.query(StockMovement).filter(StockMovement.product_id == prod_id).all()
        assert len(movements) == 2
        outgoing_movements = [m for m in movements if m.movement_type == "outgoing"]
        assert len(outgoing_movements) == 1
        assert outgoing_movements[0].amount == 7
    finally:
        db.close()


def test_concurrent_stock_in_accumulates_correctly(concurrency_client: TestClient, create_test_user):
    """
    Bir vaqtda 5 ta parallel har biri 10 birlikdan kirim qilganda:
    - Barchasi muvaffaqiyatli (200) bo'lishi
    - Hech bir yangilanish yo'qolmasligi (lost update bo'lmasligi)
    - Yakuniy qoldiq aynan 50 bo'lishi
    """
    create_test_user("staff_conc@example.com", "Password123!", role="staff")
    login_resp = concurrency_client.post(
        "/auth/login",
        data={"username": "staff_conc@example.com", "password": "Password123!"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Mahsulotni to'g'ridan-to'g'ri bazaga kiritamiz
    db = TestingSessionLocal()
    p = Product(name="Hard Drive SSD", sku="SSD-500", quantity=0, low_stock_threshold=5)
    db.add(p)
    db.commit()
    db.refresh(p)
    prod_id = p.id
    db.close()

    workers = 5
    barrier = threading.Barrier(workers)

    def perform_in():
        barrier.wait(timeout=5)
        resp = concurrency_client.post(
            f"/products/{prod_id}/stock-in",
            json={"amount": 10, "reason": "Parallel kirim"},
            headers=headers,
        )
        return resp.status_code

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(perform_in) for _ in range(workers)]
        statuses = [f.result(timeout=10) for f in futures]

    assert all(status == 200 for status in statuses)

    # Yakuniy qoldiq 50 bo'lishi kerak
    db = TestingSessionLocal()
    try:
        product = db.query(Product).filter(Product.id == prod_id).first()
        assert product.quantity == 50
    finally:
        db.close()
