# Warehouse API — Ombor Boshqaruv Tizimi Backend Loyihasi

Bu loyiha FastAPI, SQLAlchemy 2.x, PostgreSQL, Alembic va Docker yordamida yaratilgan zamonaviy, xavfsiz va to'liq testlangan backend tizimidir. Loyiha junior dasturchilar uchun tushunarli arxitektura va professional ishlab chiqarish (production) standartlariga muvofiq ishlab chiqilgan.

---

## 1. Loyiha Vazifasi

API ombordagi mahsulotlar va ularning kirim-chiqim harakatlarini boshqaradi.

Har bir muvaffaqiyatli qoldiq o'zgarishi uchun:
- Qaysi mahsulot;
- Qancha miqdor;
- Kirim yoki chiqim ekani;
- Sababi;
- Bajargan xodim (ID);
- Bajarilgan vaqt (UTC)

qat'iy tranzaksiya doirasida saqlanadi. Parallel so'rovlar vaqtida salbiy qoldiq paydo bo'lishiga yo'l qo'yilmaydi (`SELECT ... FOR UPDATE` row-level locking).

---

## 2. Texnologiyalar Staki

- **Til:** Python 3.12
- **Freymvork:** FastAPI
- **ORM:** SQLAlchemy 2.x (Synchronous Session)
- **Ma'lumotlar bazasi:** PostgreSQL 16+
- **Migratsiyalar:** Alembic
- **Validatsiya:** Pydantic 2.x
- **Autentifikatsiya:** JWT (PyJWT) + Argon2 (argon2-cffi)
- **Testlar:** pytest, HTTPX
- **Linter va Formatter:** Ruff
- **Konteynerlash:** Docker Compose
- **Deploy:** AWS EC2 (Ubuntu LTS), Nginx, systemd
- **CI/CD:** GitHub Actions

---

## 3. Papkalar Tuzilishi

```text
warehouse-api/
  app/
    main.py             # FastAPI ilovasi va asosiy endpointlar (/health)
    config.py           # Pydantic Settings (.env dan o'qish)
    database.py         # SQLAlchemy engine va SessionLocal
    dependencies.py     # JWT token tekshiruvi va rollar (user, staff, admin)
    security.py         # Argon2 parol xeshlash va JWT generatsiyasi
    models/             # SQLAlchemy ma'lumotlar bazasi modellari
      user.py           # Foydalanuvchilar jadvali
      product.py        # Mahsulotlar jadvali
      stock_movement.py # Ombor kirim-chiqim tarixi jadvali
    schemas/            # Pydantic request va response sxemalari
      auth.py           # Ro'yxatdan o'tish va login sxemalari
      user.py           # Foydalanuvchi ma'lumotlari sxemasi
      product.py        # Mahsulot CRUD sxemalari
      stock_movement.py # Kirim-chiqim va tarix sxemalari
    routers/            # API endpointlari (controllerlar)
      auth.py           # /auth/register va /auth/login
      users.py          # /users/me
      products.py       # /products (CRUD, kirim-chiqim, out-of-stock, low-stock)
      stock_movements.py# /stock-movements (tarix filtrlari)
    services/           # Biznes mantig'i va tranzaksiyalar
      auth_service.py   # Foydalanuvchi ro'yxatdan o'tkazish va tekshirish
      product_service.py# Mahsulot amallari va qidiruv
      stock_service.py  # Atomik tranzaksiyali kirim-chiqim (SELECT FOR UPDATE)
  alembic/              # Baza migratsiya fayllari
    versions/           # Migratsiya versiyalari
    env.py              # Alembic konfiguratsiyasi
  scripts/              # Ma'muriy CLI skriptlari
    create_admin.py     # Xavfsiz getpass orqali admin yaratish
    set_user_role.py    # Xodimga 'staff' yoki 'admin' roli berish
  tests/                # Avtomatik testlar (31 ta test)
    conftest.py         # Test muhiti va PostgreSQL fixturalari
    test_auth.py        # Autentifikatsiya testlari
    test_permissions.py # Rollar va ruxsatlar testlari
    test_products.py    # Mahsulot CRUD va qoldiq hisoboti testlari
    test_stock_movements.py # Tranzaksiyali kirim-chiqim testlari
    test_concurrency.py # Haqiqiy parallel tranzaksiya testlari
  deploy/               # Serverga o'rnatish fayllari
    nginx.conf          # Nginx reverse proxy sozlamasi
    warehouse-api.service # Systemd servisi
    deploy.sh           # Avtomatik yangilanish skripti
    bootstrap.sh        # Yangi EC2 serverini sozlash skripti
  .github/workflows/
    ci-cd.yml           # GitHub Actions avtomatik test va deploy workflow
  alembic.ini           # Alembic asosiy konfiguratsiyasi
  compose.yaml          # Lokal PostgreSQL uchun Docker Compose
  requirements.txt      # Asosiy kutubxonalar
  requirements-dev.txt  # Test va ishlab chiqish kutubxonalari
  pyproject.toml        # Ruff va Pytest sozlamalari
  .env.example          # Muhit o'zgaruvchilari namunasi
  .gitignore            # Git dan yashiriladigan fayllar
  README.md             # Asosiy qo'llanma
  EXPLANATION.md        # Nazariy tushuntirishlar va arxitektura
  DEMO.md               # Himoya uchun bosqichma-bosqich ssenariy
```

---

## 4. Rollar va Ruxsatlar Jadvali

| Endpoint | Metod | Tavsif | user | staff | admin |
| :--- | :---: | :--- | :---: | :---: | :---: |
| `/health` | GET | Tizim salomatligi (baza tekshiruvi) | Ochiq | Ochiq | Ochiq |
| `/auth/register` | POST | Ro'yxatdan o'tish (faqat `user` roli) | Ochiq | Ochiq | Ochiq |
| `/auth/login` | POST | Login qilib Bearer token olish | Ochiq | Ochiq | Ochiq |
| `/users/me` | GET | Joriy foydalanuvchi profili | Ha | Ha | Ha |
| `/products` | POST | Yangi mahsulot yaratish | Yo'q (403) | Yo'q (403) | **Ha** |
| `/products` | GET | Mahsulotlar ro'yxati va qidiruv | Yo'q (403) | **Ha** | **Ha** |
| `/products/out-of-stock` | GET | Qoldig'i 0 bo'lgan mahsulotlar | Yo'q (403) | **Ha** | **Ha** |
| `/products/low-stock` | GET | Qoldig'i kam mahsulotlar | Yo'q (403) | **Ha** | **Ha** |
| `/products/{id}` | GET | Mahsulot tafsilotlari | Yo'q (403) | **Ha** | **Ha** |
| `/products/{id}` | PATCH | Mahsulotni tahrirlash (nom, sku, chegara) | Yo'q (403) | Yo'q (403) | **Ha** |
| `/products/{id}` | DELETE | Mahsulotni o'chirish (tarixi yo'q bo'lsa) | Yo'q (403) | Yo'q (403) | **Ha** |
| `/products/{id}/stock-in` | POST | Kirim qilish | Yo'q (403) | **Ha** | **Ha** |
| `/products/{id}/stock-out`| POST | Chiqim qilish | Yo'q (403) | **Ha** | **Ha** |
| `/stock-movements` | GET | Harakatlar tarixi va filtrlar | Yo'q (403) | **Ha** | **Ha** |

---

## 5. Lokal O'rnatish va Ishga Tushirish

### A. Windows PowerShell uchun:

```powershell
# 1. Loyiha papkasiga o'tish
cd "C:\Users\Windows 11\Desktop\fast_api loyiha\warehouse-api"

# 2. Virtual muhit yaratish va faollashtirish
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Paketlarni o'rnatish
pip install -r requirements-dev.txt

# 4. .env faylini yaratish
Copy-Item .env.example .env

# 5. PostgreSQL bazasini ishga tushirish (Docker orqali):
docker compose up -d
# Yoki mahalliy PostgreSQL ishlayotgan bo'lsa, .env dagi DATABASE_URL ni sozlang

# 6. Alembic migratsiyasini bajarish
alembic upgrade head

# 7. Birinchi Admin foydalanuvchini yaratish
python scripts/create_admin.py

# 8. Ilovani ishga tushirish
uvicorn app.main:app --reload --port 8000
```

### B. Linux (Ubuntu) uchun:

```bash
# 1. Virtual muhit yaratish va faollashtirish
python3 -m venv .venv
source .venv/bin/activate

# 2. Paketlarni o'rnatish
pip install -r requirements-dev.txt

# 3. .env faylini tayyorlash
cp .env.example .env

# 4. Migratsiyalarni qo'llash
alembic upgrade head

# 5. Admin yaratish
python scripts/create_admin.py

# 6. Ilovani ishga tushirish
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 6. Xodimlarga Rol Berish (CLI)

Ochiq ro'yxatdan o'tgan foydalanuvchiga `staff` rolini berish uchun serverda quyidagi buyruq bajariladi:

```bash
python scripts/set_user_role.py
# Email: xodim@example.com
# Yangi rol: staff
```

---

## 7. Testlar va Sifat Tekshiruvi

Barcha testlar haqiqiy alohida PostgreSQL bazasida bajariladi:

```powershell
# Barcha 31 ta testni ishga tushirish:
pytest -v

# Kod sifatini Ruff orqali tekshirish:
ruff check .

# Kod formatini tekshirish:
ruff format --check .
```

---

## 8. GitHub Actions CI/CD Sozlamalari

Har safar `main` branchga push yoki Pull Request bo'lganda quyidagi bosqichlar avtomatik ishlaydi:
1. Ruff lint va format tekshiruvi.
2. PostgreSQL service container yaratish.
3. Bo'sh test bazada `alembic upgrade head` migratsiyasini tekshirish.
4. Concurrency va ruxsatlarni o'z ichiga olgan barcha pytest testlarini bajarish.
5. Faqat `main` push bo'lganda va testlar muvaffaqiyatli o'tsa, SSH orqali AWS EC2 ga deploy qilish.

### Talab qilinadigan GitHub Secrets:
GitHub repository sozlamalarida (`Settings -> Secrets and variables -> Actions`) quyidagi o'zgaruvchilarni qo'shing:
- `EC2_HOST`: AWS EC2 serveringizning ommaviy IP manzili (masalan: `54.123.45.67`)
- `EC2_USER`: Server foydalanuvchisi (odatda Ubuntu uchun `ubuntu`)
- `EC2_SSH_KEY`: Serverga ulanish uchun shaxsiy SSH kalitingiz (`.pem` fayl ichidagi matn)
- `EC2_KNOWN_HOSTS`: Serverning SSH host fingerprint kaliti (`ssh-keyscan -H <EC2_HOST>` orqali olinadi)

---

## 9. AWS EC2 Serverida Deploy Qilish

1. EC2 Ubuntu LTS server yarating.
2. Serverga ulaning va `deploy/bootstrap.sh` ni ishga tushiring:
   ```bash
   bash /opt/warehouse-api/deploy/bootstrap.sh
   ```
3. `/opt/warehouse-api/.env` fayliga ishlab chiqarish kalitlarini yozing.
4. Server holatini tekshirish:
   ```bash
   sudo systemctl status warehouse-api
   curl http://localhost:8000/health
   ```
5. Loglarni ko'rish:
   ```bash
   sudo journalctl -u warehouse-api -f
   ```

---

## 10. Ko'p Uchraydigan Xatolar va Yechimlar

1. **401 Unauthorized "Email yoki parol noto'g'ri":**
   - Parol xeshi mos kelmagan yoki email ro'yxatdan o'tmagan. Swagger Authorize tugmasida `username` maydoniga email kiritilishi kerak.
2. **409 Conflict "Omborda yetarli qoldiq mavjud emas":**
   - Chiqim miqdori joriy ombor qoldig'idan katta bo'lganda yuzaga keladi. Bu biznes qoidasidir.
3. **409 Conflict "Ushbu mahsulotda ombor harakatlari tarixi mavjud":**
   - Mahsulot o'chirib yuborilganda audit tarixi yo'qolmasligi uchun `ON DELETE RESTRICT` o'rnatilgan. Tarixli mahsulotni o'chirib bo'lmaydi.
4. **422 Unprocessable Entity "Extra inputs are not permitted":**
   - Pydantic `extra="forbid"` qoidasi tufayli ruxsat berilmagan maydonlar yuborilganda (masalan, registerda `role`, mahsulot yaratishda `quantity`).
