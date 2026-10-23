from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_stock_in_out_workflow_and_insufficient_stock(
    client: TestClient, admin_token: str, staff_token: str, db_session: Session
):
    """
    Klassik ombor oqimi:
    - 10 kirim
    - 4 chiqim -> qoldiq 6
    - 7 chiqimga urinish -> 409
    - Yakuniy qoldiq hali ham 6
    - Tarixda faqat 2 ta muvaffaqiyatli harakat
    """
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    # 1. Admin mahsulot yaratadi (quantity = 0)
    p = client.post("/products", json={"name": "Widget", "sku": "WDG-01"}, headers=admin_headers).json()
    prod_id = p["id"]

    # 2. Staff 10 birlik kirim qiladi
    resp_in = client.post(
        f"/products/{prod_id}/stock-in",
        json={"amount": 10, "reason": "10 dona keldi"},
        headers=staff_headers,
    )
    assert resp_in.status_code == 200
    assert resp_in.json()["updated_quantity"] == 10

    # 3. Staff 4 birlik chiqim qiladi
    resp_out = client.post(
        f"/products/{prod_id}/stock-out",
        json={"amount": 4, "reason": "4 dona sotildi"},
        headers=staff_headers,
    )
    assert resp_out.status_code == 200
    assert resp_out.json()["updated_quantity"] == 6

    # 4. Detail orqali qoldiq 6 ekanini tekshiramiz
    detail_resp = client.get(f"/products/{prod_id}", headers=staff_headers)
    assert detail_resp.json()["quantity"] == 6

    # 5. Qoldiq 6 bo'lganda 7 birlik chiqim qilishga urinish -> 409
    fail_out = client.post(
        f"/products/{prod_id}/stock-out",
        json={"amount": 7, "reason": "7 dona berishga urinish"},
        headers=staff_headers,
    )
    assert fail_out.status_code == 409
    assert "yetarli qoldiq mavjud emas" in fail_out.json()["detail"]

    # 6. Qoldiq o'zgarmaganligini tekshiramiz (hali ham 6)
    detail_after = client.get(f"/products/{prod_id}", headers=staff_headers)
    assert detail_after.json()["quantity"] == 6

    # 7. Tarixda faqat 2 ta yozuv borligini tekshiramiz (rad etilgan 7 chiqim tarixga kirmagan)
    history_resp = client.get(f"/stock-movements?product_id={prod_id}", headers=staff_headers)
    assert history_resp.status_code == 200
    items = history_resp.json()["items"]
    assert len(items) == 2
    # Yozuvlar sababi va xodim ID tekshiruvi
    assert items[0]["movement_type"] == "outgoing"
    assert items[0]["amount"] == 4
    assert items[0]["reason"] == "4 dona sotildi"
    assert items[0]["performed_by_id"] is not None

    assert items[1]["movement_type"] == "incoming"
    assert items[1]["amount"] == 10
    assert items[1]["reason"] == "10 dona keldi"


def test_stock_movement_invalid_amount_inputs(client: TestClient, admin_token: str):
    """amount: 0, manfiy, kasr, bool va string bo'lganda 422 rad etilishi."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    p = client.post("/products", json={"name": "Item", "sku": "ITM-VAL"}, headers=headers).json()
    prod_id = p["id"]

    invalid_amounts = [
        0,  # Nol
        -5,  # Manfiy son
        3.14,  # Kasr son
        True,  # Boolean
        "10",  # String
    ]

    for val in invalid_amounts:
        resp = client.post(
            f"/products/{prod_id}/stock-in",
            json={"amount": val, "reason": "Test"},
            headers=headers,
        )
        assert resp.status_code == 422, f"Expected 422 for amount={val}, got {resp.status_code}"


def test_stock_movement_empty_reason_rejected(client: TestClient, admin_token: str):
    """Bo'sh yoki faqat bo'shliqlardan iborat reason 422 bo'lishi kerak."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    p = client.post("/products", json={"name": "Item", "sku": "ITM-RSN"}, headers=headers).json()
    prod_id = p["id"]

    resp1 = client.post(
        f"/products/{prod_id}/stock-in",
        json={"amount": 5, "reason": ""},
        headers=headers,
    )
    assert resp1.status_code == 422

    resp2 = client.post(
        f"/products/{prod_id}/stock-in",
        json={"amount": 5, "reason": "   "},
        headers=headers,
    )
    assert resp2.status_code == 422


def test_stock_movement_rejects_extra_fields(client: TestClient, admin_token: str):
    """Client performed_by_id yoki quantity yuborishi rad etilishi kerak (422)."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    p = client.post("/products", json={"name": "Item", "sku": "ITM-EXT"}, headers=headers).json()
    prod_id = p["id"]

    resp = client.post(
        f"/products/{prod_id}/stock-in",
        json={"amount": 5, "reason": "Partiya", "performed_by_id": 999},
        headers=headers,
    )
    assert resp.status_code == 422


def test_history_date_filtering(client: TestClient, admin_token: str):
    """Tarixni sana oralig'i bo'yicha to'g'ri filtrlash."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    p = client.post("/products", json={"name": "Item", "sku": "ITM-DATE"}, headers=headers).json()
    prod_id = p["id"]

    client.post(
        f"/products/{prod_id}/stock-in",
        json={"amount": 5, "reason": "Bugungi kirim"},
        headers=headers,
    )

    today = date.today()
    tomorrow = today + timedelta(days=1)
    yesterday = today - timedelta(days=1)

    # Bugungi sana oralig'i: kiritilishi kerak
    resp = client.get(
        f"/stock-movements?product_id={prod_id}&date_from={today}&date_to={today}",
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 1

    # date_from > date_to bo'lsa 422
    resp_invalid = client.get(
        f"/stock-movements?date_from={tomorrow}&date_to={yesterday}",
        headers=headers,
    )
    assert resp_invalid.status_code == 422


def test_stock_movements_immutable(client: TestClient, admin_token: str):
    """StockMovement endpointlarida PATCH, PUT, DELETE yo'qligi (tarix o'zgarmas)."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    # Tarixni o'zgartirish yoki o'chirishga qilingan urinishlar 404 yoki 405 bo'lishi kerak
    assert client.patch("/stock-movements/1", json={}, headers=headers).status_code in (404, 405)
    assert client.delete("/stock-movements/1", headers=headers).status_code in (404, 405)
