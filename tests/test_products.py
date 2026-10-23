from fastapi.testclient import TestClient


def test_create_product_initial_quantity_zero(client: TestClient, admin_token: str):
    """Mahsulot yaratilganda boshlang'ich quantity doimo 0 bo'lishi kerak."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.post(
        "/products",
        json={
            "name": "Monitor 24 inch",
            "sku": "MON-24",
            "description": "Full HD IPS Monitor",
            "low_stock_threshold": 5,
        },
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["quantity"] == 0
    assert data["name"] == "Monitor 24 inch"
    assert data["sku"] == "MON-24"
    assert data["low_stock_threshold"] == 5


def test_create_product_rejects_client_quantity(client: TestClient, admin_token: str):
    """Yaratish paytida client quantity yuborsa 422 bilan rad etilishi kerak."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.post(
        "/products",
        json={
            "name": "Monitor",
            "sku": "MON-01",
            "quantity": 100,  # Taqiqlangan maydon!
        },
        headers=headers,
    )
    assert response.status_code == 422


def test_patch_product_rejects_client_quantity(client: TestClient, admin_token: str):
    """PATCH so'rovida quantity yuborilsa 422 bilan rad etilishi kerak."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    p = client.post(
        "/products",
        json={"name": "Cable", "sku": "CBL-01"},
        headers=headers,
    ).json()

    response = client.patch(
        f"/products/{p['id']}",
        json={"quantity": 50},  # Taqiqlangan maydon!
        headers=headers,
    )
    assert response.status_code == 422


def test_sku_case_normalisation_and_duplicate(client: TestClient, admin_token: str):
    """SKU trim va uppercase bo'lishi hamda takroriy bo'lsa 409 berishi."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp1 = client.post(
        "/products",
        json={"name": "Item A", "sku": "  abc-001  "},
        headers=headers,
    )
    assert resp1.status_code == 201
    assert resp1.json()["sku"] == "ABC-001"

    # Bir xil SKU boshqa ko'rinishda yuborilganda
    resp2 = client.post(
        "/products",
        json={"name": "Item B", "sku": "ABC-001"},
        headers=headers,
    )
    assert resp2.status_code == 409


def test_invalid_low_stock_threshold(client: TestClient, admin_token: str):
    """Manfiy yoki noto'g'ri turdagi low_stock_threshold rad etilishi (422)."""
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Manfiy son
    resp1 = client.post(
        "/products",
        json={"name": "Item", "sku": "SKU-N1", "low_stock_threshold": -5},
        headers=headers,
    )
    assert resp1.status_code == 422

    # String formatidagi son (strict=True)
    resp2 = client.post(
        "/products",
        json={"name": "Item", "sku": "SKU-N2", "low_stock_threshold": "five"},
        headers=headers,
    )
    assert resp2.status_code == 422


def test_product_search_and_pagination(client: TestClient, admin_token: str):
    """Mahsulotlarni qidirish va paginatsiya tekshiruvi."""
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 3 ta mahsulot yaratamiz
    client.post("/products", json={"name": "Gaming Keyboard RGB", "sku": "KB-RGB-01"}, headers=headers)
    client.post("/products", json={"name": "Office Keyboard Silent", "sku": "KB-SLN-02"}, headers=headers)
    client.post("/products", json={"name": "Ergonomic Mouse", "sku": "MS-ERG-01"}, headers=headers)

    # Qidiruv: "keyboard" (case-insensitive)
    resp_search = client.get("/products?search=keyboard", headers=headers)
    assert resp_search.status_code == 200
    data = resp_search.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2

    # SKU bo'yicha qidiruv: "ms-erg"
    resp_sku = client.get("/products?search=ms-erg", headers=headers)
    assert resp_sku.status_code == 200
    assert resp_sku.json()["total"] == 1

    # Paginatsiya: limit=1, offset=1
    resp_page = client.get("/products?limit=1&offset=1", headers=headers)
    assert resp_page.status_code == 200
    assert resp_page.json()["total"] == 3
    assert len(resp_page.json()["items"]) == 1
    assert resp_page.json()["limit"] == 1
    assert resp_page.json()["offset"] == 1


def test_product_detail_not_found(client: TestClient, admin_token: str):
    """Mavjud bo'lmagan mahsulot ID so'ralganda 404."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get("/products/999999", headers=headers)
    assert response.status_code == 404


def test_delete_product_with_history_rejected(client: TestClient, admin_token: str):
    """Harakat tarixi bo'lgan mahsulotni o'chirish 409 berishi shart."""
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Mahsulot yaratamiz
    p = client.post("/products", json={"name": "Hard Drive", "sku": "HDD-01"}, headers=headers).json()
    prod_id = p["id"]

    # Kirim amali bajaramiz (tarix yoziladi)
    client.post(
        f"/products/{prod_id}/stock-in",
        json={"amount": 5, "reason": "Boshlang'ich qoldiq"},
        headers=headers,
    )

    # O'chirishga urinamiz -> 409
    del_resp = client.delete(f"/products/{prod_id}", headers=headers)
    assert del_resp.status_code == 409
    assert "tarixi mavjud" in del_resp.json()["detail"]


def test_out_of_stock_and_low_stock_filters(client: TestClient, admin_token: str):
    """Out-of-stock (quantity=0) va low-stock (0 < quantity <= threshold) tekshiruvi."""
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Mahsulot 1: quantity = 0, threshold = 5 (Out of stock)
    p1 = client.post(
        "/products",
        json={"name": "Item Zero", "sku": "SKU-00", "low_stock_threshold": 5},
        headers=headers,
    ).json()

    # Mahsulot 2: quantity = 3, threshold = 5 (Low stock)
    p2 = client.post(
        "/products",
        json={"name": "Item Low", "sku": "SKU-LOW", "low_stock_threshold": 5},
        headers=headers,
    ).json()
    client.post(f"/products/{p2['id']}/stock-in", json={"amount": 3, "reason": "Partiya 1"}, headers=headers)

    # Mahsulot 3: quantity = 5, threshold = 5 (Low stock - thresholdga teng!)
    p3 = client.post(
        "/products",
        json={"name": "Item Equal", "sku": "SKU-EQ", "low_stock_threshold": 5},
        headers=headers,
    ).json()
    client.post(f"/products/{p3['id']}/stock-in", json={"amount": 5, "reason": "Partiya 2"}, headers=headers)

    # Mahsulot 4: quantity = 20, threshold = 5 (Normal stock)
    p4 = client.post(
        "/products",
        json={"name": "Item Normal", "sku": "SKU-NORM", "low_stock_threshold": 5},
        headers=headers,
    ).json()
    client.post(
        f"/products/{p4['id']}/stock-in",
        json={"amount": 20, "reason": "Partiya 3"},
        headers=headers,
    )

    # 1. Out-of-stock tekshiruvi (faqat quantity = 0 bo'lganlar)
    out_resp = client.get("/products/out-of-stock", headers=headers)
    assert out_resp.status_code == 200
    out_items = out_resp.json()["items"]
    assert len(out_items) == 1
    assert out_items[0]["id"] == p1["id"]

    # 2. Low-stock tekshiruvi (0 < quantity <= threshold)
    # Muhim talab: quantity = 0 bu ro'yxatga kirmasligi kerak!
    low_resp = client.get("/products/low-stock", headers=headers)
    assert low_resp.status_code == 200
    low_items = low_resp.json()["items"]
    assert len(low_items) == 2
    low_ids = [item["id"] for item in low_items]
    assert p2["id"] in low_ids
    assert p3["id"] in low_ids
    assert p1["id"] not in low_ids  # Quantity = 0 bo'lgan mahsulot low-stock ro'yxatiga kirmaydi!
    assert p4["id"] not in low_ids
