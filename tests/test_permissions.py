from fastapi.testclient import TestClient


def test_unauthenticated_request_returns_401(client: TestClient):
    """Tokensiz himoyalangan endpointlarga so'rov 401 qaytarishi."""
    resp1 = client.get("/products")
    assert resp1.status_code == 401

    resp2 = client.post("/products", json={"name": "P", "sku": "SKU1"})
    assert resp2.status_code == 401

    resp3 = client.get("/stock-movements")
    assert resp3.status_code == 401


def test_regular_user_cannot_access_warehouse_apis(client: TestClient, user_token: str):
    """Oddiy 'user' ombor APIlariga kira olmasligi (barchasidan 403 olishi)."""
    headers = {"Authorization": f"Bearer {user_token}"}

    # Mahsulotlar ro'yxatiga kira olmaydi
    assert client.get("/products", headers=headers).status_code == 403
    # Mahsulot yarata olmaydi
    assert (
        client.post(
            "/products",
            json={"name": "Item", "sku": "ITM-01"},
            headers=headers,
        ).status_code
        == 403
    )
    # Hisobotlarga kira olmaydi
    assert client.get("/products/out-of-stock", headers=headers).status_code == 403
    assert client.get("/products/low-stock", headers=headers).status_code == 403
    # Tarixga kira olmaydi
    assert client.get("/stock-movements", headers=headers).status_code == 403


def test_staff_cannot_create_update_or_delete_products(client: TestClient, admin_token: str, staff_token: str):
    """Staff mahsulot yarata olmaydi, tahrirlay olmaydi va o'chira olmaydi (403)."""
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    # 1. Admin mahsulot yaratadi
    create_resp = client.post(
        "/products",
        json={"name": "Scanner", "sku": "SCN-100", "low_stock_threshold": 3},
        headers=admin_headers,
    )
    assert create_resp.status_code == 201
    prod_id = create_resp.json()["id"]

    # 2. Staff yangi mahsulot yarata olmaydi (403)
    assert (
        client.post(
            "/products",
            json={"name": "Staff Item", "sku": "STF-01"},
            headers=staff_headers,
        ).status_code
        == 403
    )

    # 3. Staff mahsulotni tahrirlay olmaydi (403)
    assert (
        client.patch(
            f"/products/{prod_id}",
            json={"name": "Scanner Updated"},
            headers=staff_headers,
        ).status_code
        == 403
    )

    # 4. Staff mahsulotni o'chira olmaydi (403)
    assert client.delete(f"/products/{prod_id}", headers=staff_headers).status_code == 403


def test_staff_can_view_and_operate_stock(client: TestClient, admin_token: str, staff_token: str):
    """Staff mahsulotlarni ko'ra oladi, kirim/chiqim qila oladi va tarixni ko'ra oladi."""
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    # Admin mahsulot yaratadi
    p = client.post(
        "/products",
        json={"name": "Mouse", "sku": "MS-001", "low_stock_threshold": 2},
        headers=admin_headers,
    ).json()
    prod_id = p["id"]

    # Staff ro'yxatni ko'radi
    list_resp = client.get("/products", headers=staff_headers)
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 1

    # Staff kirim qiladi
    in_resp = client.post(
        f"/products/{prod_id}/stock-in",
        json={"amount": 10, "reason": "Yangi partiya keldi"},
        headers=staff_headers,
    )
    assert in_resp.status_code == 200
    assert in_resp.json()["updated_quantity"] == 10

    # Staff chiqim qiladi
    out_resp = client.post(
        f"/products/{prod_id}/stock-out",
        json={"amount": 3, "reason": "Mijozga sotildi"},
        headers=staff_headers,
    )
    assert out_resp.status_code == 200
    assert out_resp.json()["updated_quantity"] == 7

    # Staff tarixni ko'radi
    hist_resp = client.get("/stock-movements", headers=staff_headers)
    assert hist_resp.status_code == 200
    assert hist_resp.json()["total"] == 2


def test_admin_full_permissions(client: TestClient, admin_token: str):
    """Admin yaratish, tahrirlash, o'chirish huquqlariga to'liq ega."""
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Yaratish
    p = client.post(
        "/products",
        json={"name": "Printer", "sku": "PRN-001", "low_stock_threshold": 2},
        headers=headers,
    ).json()
    prod_id = p["id"]

    # Tahrirlash
    edit_resp = client.patch(
        f"/products/{prod_id}",
        json={"name": "Laser Printer", "low_stock_threshold": 4},
        headers=headers,
    )
    assert edit_resp.status_code == 200
    assert edit_resp.json()["name"] == "Laser Printer"
    assert edit_resp.json()["low_stock_threshold"] == 4

    # O'chirish (tarixi yo'qligi sababli muvaffaqiyatli 204)
    del_resp = client.delete(f"/products/{prod_id}", headers=headers)
    assert del_resp.status_code == 204

    # Endi topilmaydi (404)
    assert client.get(f"/products/{prod_id}", headers=headers).status_code == 404
