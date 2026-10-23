# Warehouse API — Himoya uchun Bosqichma-bosqich Demo Ssenariysi (DEMO.md)

Ushbu qo'llanma loyiha himoyasida yoki tekshiruvchiga tizimning to'liq ishlashini Swagger UI (`http://127.0.0.1:8000/docs`) orqali ketma-ket namoyish qilish uchun tayyorlangan.

---

## Dastlabki Tayyorgarlik

Serverni ishga tushiring:
```powershell
uvicorn app.main:app --reload --port 8000
```
Brauzerda oching: **`http://127.0.0.1:8000/docs`**

---

### 1-Qadam: Admin Bilan Login Qilish
1. Swagger tepasidagi yashil **`Authorize`** tugmasini bosing.
2. `username`: `admin@example.com`
3. `password`: CLI orqali yaratilgan admin paroli (masalan, `AdminPassword123!`).
4. **`Authorize`** tugmasini bosing va oynani yoping. Endi barcha so'rovlar Admin nomidan boradi.

---

### 2-Qadam: Yangi Mahsulot Yaratish (Boshlang'ich Quantity = 0)
1. **`POST /products`** oching -> **`Try it out`**.
2. JSON tanasiga yozing:
   ```json
   {
     "name": "Mexanik Klaviatura RGB",
     "sku": "KB-MECH-01",
     "description": "Red switch mexanik klaviatura",
     "low_stock_threshold": 5
   }
   ```
3. **`Execute`** bosing.
4. **Kutilgan natija (201 Created):**
   ```json
   {
     "id": 1,
     "name": "Mexanik Klaviatura RGB",
     "sku": "KB-MECH-01",
     "quantity": 0,
     "low_stock_threshold": 5
   }
   ```
   *E'tibor bering: Quantity mijoz tomonidan kiritilmadi, u avtomatik `0` bo'lib yaratildi.*

---

### 3-Qadam: Staff Xodimi Bilan Login Qilish
1. Swagger tepasidagi **`Authorize`** tugmasini bosib, **`Logout`** qiling.
2. Endi Staff xodimi bilan kiring:
   - `username`: `staff@example.com`
   - `password`: `StaffPassword123!`
3. **`Authorize`** bosing.

---

### 4-Qadam: 10 Birlik Kirim Qilish
1. **`POST /products/{product_id}/stock-in`** oching.
2. `product_id`: `1`
3. So'rov tanasi:
   ```json
   {
     "amount": 10,
     "reason": "Yetkazib beruvchidan yangi partiya qabul qilindi"
   }
   ```
4. **`Execute`** bosing.
5. **Kutilgan natija (200 OK):**
   - `updated_quantity`: `10`
   - `movement`: yo'nalishi `incoming`, miqdori `10`.

---

### 5-Qadam: 4 Birlik Chiqim Qilish
1. **`POST /products/{product_id}/stock-out`** oching.
2. `product_id`: `1`
3. So'rov tanasi:
   ```json
   {
     "amount": 4,
     "reason": "Filialga jo'natildi"
   }
   ```
4. **`Execute`** bosing.
5. **Kutilgan natija (200 OK):**
   - `updated_quantity`: `6`
   - `movement`: yo'nalishi `outgoing`, miqdori `4`.

---

### 6-Qadam: Mahsulot Detailida Qoldiq 6 Ekanini Ko'rsatish
1. **`GET /products/1`** oching -> **`Execute`**.
2. **Kutilgan natija (200 OK):**
   - `"quantity": 6`

---

### 7-Qadam: 7 Birlik Chiqim Qilishga Urinish (Qoldiqdan Ortiq — 409)
1. **`POST /products/{product_id}/stock-out`** oching.
2. `product_id`: `1`
3. So'rov tanasi:
   ```json
   {
     "amount": 7,
     "reason": "Mijoz buyurtmasi"
   }
   ```
4. **`Execute`** bosing.
5. **Kutilgan natija (409 Conflict):**
   ```json
   {
     "detail": "Omborda yetarli qoldiq mavjud emas. Joriy qoldiq: 6, talab qilingan: 7"
   }
   ```

---

### 8-Qadam: Qoldiq Hali Ham 6 Ekanini Tekshirish
1. **`GET /products/1`** oching -> **`Execute`**.
2. **Kutilgan natija (200 OK):**
   - `"quantity": 6` (Muvaffaqiyatsiz so'rov qoldiqni o'zgartirmadi).

---

### 9 & 10-Qadam: Tarixda Faqat 2 ta Harakat Borligi, Sabab va Xodimni Ko'rsatish
1. **`GET /stock-movements`** oching -> `product_id: 1` -> **`Execute`**.
2. **Kutilgan natija (200 OK):**
   - `"total": 2` (Rad etilgan 7 chiqim tarixga kirmagan!)
   - 1-yozuv: `outgoing`, amount: `4`, reason: `"Filialga jo'natildi"`, performed_by_id: `<staff_id>`.
   - 2-yozuv: `incoming`, amount: `10`, reason: `"Yetkazib beruvchidan yangi partiya qabul qilindi"`.

---

### 11-Qadam: Staff Mahsulotni Tahrirlay Olmasligini Ko'rsatish (403)
1. Hozirgi `staff` tokeni bilan **`PATCH /products/1`** oching.
2. So'rov tanasi:
   ```json
   {
     "name": "Buzg'unchi Nom"
   }
   ```
3. **`Execute`** bosing.
4. **Kutilgan natija (403 Forbidden):**
   ```json
   {
     "detail": "Ushbu amalni bajarish uchun huquqingiz yetarli emas"
   }
   ```

---

### 12-Qadam: Ro'yxatdan O'tishda Admin Bo'lib Bo'lmasligini Ko'rsatish (422)
1. **`POST /auth/register`** oching.
2. So'rov tanasi:
   ```json
   {
     "email": "attacker@example.com",
     "password": "Password123!",
     "role": "admin"
   }
   ```
3. **`Execute`** bosing.
4. **Kutilgan natija (422 Unprocessable Entity):**
   - Pydantic qo'shimcha `role` maydonini qat'iy rad etadi (`extra='forbid'`).

---

### 13-Qadam: Quantity'ni PATCH Orqali O'zgartirib Bo'lmasligini Ko'rsatish (422)
1. Admin tokeni bilan kiring.
2. **`PATCH /products/1`** oching.
3. So'rov tanasi:
   ```json
   {
     "quantity": 1000
   }
   ```
4. **`Execute`** bosing.
5. **Kutilgan natija (422 Unprocessable Entity):**
   - Quantity faqatgina audit qilingan kirim-chiqim orqali o'zgaradi!

---

### 14-Qadam: Out-of-Stock va Low-Stock Hisobotlarini Ko'rsatish
1. **`GET /products/out-of-stock`**: Faqat `quantity = 0` bo'lgan mahsulotlar chiqadi.
2. **`GET /products/low-stock`**: Qoldig'i `0 < quantity <= low_stock_threshold` bo'lgan mahsulotlar chiqadi (bizning klaviatura qoldig'i 6, threshold 5 bo'lgani uchun hali kam qolganlar ro'yxatiga kirmaydi).

---

### 15-Qadam: Tarixni Mahsulot va Sana Bo'yicha Filtrlash
1. **`GET /stock-movements`** oching.
2. Parametrlar:
   - `date_from`: bugungi sana (masalan: `2026-10-23`)
   - `date_to`: bugungi sana
   - `movement_type`: `incoming`
3. **`Execute`** bosing -> Faqat bugungi kirim yozuvi chiqadi.

---

### 16-Qadam: GitHub Actions CI/CD Muvaffaqiyatli Run
- GitHub repozitoriyasining **Actions** bo'limida avtomatik testlar va lint 100% yashil o'tganini ko'rsatish.

---

### 17-Qadam: AWS EC2 Serverida `/health` va `/docs`
- Brauzerda server IP manzili orqali ochib ko'rsatish:
  - `http://<EC2_IP>/health` -> `{"status": "ok", "database": "connected"}`
  - `http://<EC2_IP>/docs` -> Swagger UI to'liq ishlayotgani.
