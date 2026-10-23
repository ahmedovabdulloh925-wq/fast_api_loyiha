# Backend Asoslari va Arxitektura Tushuntirishlari (EXPLANATION.md)

Ushbu hujjat backend sohasini endi o'rganayotgan junior dasturchilar uchun yozilgan bo'lib, loyihamizda qo'llanilgan har bir tushunchani aynan bizning kodimizdagi misollar orqali oddiy va tushunarli qilib izohlaydi.

---

## 1. Model nima? (SQLAlchemy Model)

**Model** — bu Python klassi ko'rinishidagi ma'lumotlar bazasi jadvalidir. Biz SQL buyruqlarini (masalan, `CREATE TABLE`, `INSERT`) qo'lda yozmasdan, Python kodida jadval qanday ustunlardan iborat bo'lishini tasvirlaymiz.

**Bizning koddagi misol (`app/models/product.py`):**
```python
class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=0)
```
Bu yerda `Product` klassi PostgreSQL dagi `products` jadvaliga mos keladi. Har bir `Product` obyekti bazadagi bitta qatordir.

---

## 2. Sxema nima? (Pydantic Schema)

**Sxema** — bu tarmoqdan (front-end yoki foydalanuvchidan) keladigan ma'lumotlarni tekshiruvchi (validatsiya qiluvchi) va javobda nimalar qaytishini cheklovchi qolipdir.

**Model va Sxema farqi:**
- **Model** ma'lumotlar bazasida qanday saqlanishini belgilaydi.
- **Sxema** tarmoq orqali qanday qabul qilinishi va chiqarilishini belgilaydi.
- *Misol:* Bazadagi `User` modelida `password_hash` bor, lekin `UserResponse` sxemasida bu maydon yo'q. Shuning uchun parollar foydalanuvchiga hech qachon oshkor bo'lmaydi!

**Bizning koddagi misol (`app/schemas/stock_movement.py`):**
```python
class StockMovementCreate(BaseModel):
    amount: int = Field(gt=0, strict=True) # Faqat musbat butun son!
    reason: str = Field(min_length=1)      # Bo'sh bo'lishi mumkin emas
```

---

## 3. Router nima? (API Endpoints)

**Router** — bu kelgan HTTP so'rovlarni (URL va metod: `GET`, `POST`, `PATCH`, `DELETE`) qabul qilib, ularni qaysi funksiya bajarishi kerakligini belgilaydigan "yo'l ko'rsatuvchi"dir.

**Bizning koddagi misol (`app/routers/products.py`):**
```python
@router.post("/{product_id}/stock-in")
def stock_in(product_id: int, data: StockMovementCreate, db: Session = Depends(get_db)):
    ...
```
Foydalanuvchi `POST /products/1/stock-in` ga murojaat qilganda, FastAPI aynan shu funksiyani ishga tushiradi.

---

## 4. Service nima? (Biznes Mantig'i)

**Service** — bu loyihaning asosiy biznes qoidalarini bajaradigan qatlam. Router faqat so'rovni qabul qilib javob qaytaradi, qoldiqni hisoblash, yetarliligini tekshirish va bazaga yozish kabi muhim ishlarni esa Service bajaradi.

**Bizning koddagi misol (`app/services/stock_service.py`):**
```python
def perform_stock_out(db, product_id, user_id, amount, reason):
    # 1. Mahsulotni topish
    # 2. Qoldiq yetarliligini tekshirish
    if product.quantity < amount:
        raise HTTPException(status_code=409, detail="Yetarli qoldiq mavjud emas")
    # 3. Qoldiqni ayirish va tarix yozish
```

---

## 5. Dependency Injection nima? (`Depends`)

**Dependency** — biror funksiya ishlashi uchun zarur bo'lgan resurs (masalan, ma'lumotlar bazasi sessiyasi yoki autentifikatsiyadan o'tgan foydalanuvchi). FastAPI `Depends()` mexanizmi orqali buni avtomatik tarzda taqdim etadi.

**Bizning koddagi misol (`app/dependencies.py`):**
```python
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    # Tokendan foydalanuvchini topadi
```
Endpointda `current_user: User = Depends(get_current_user)` deb yozsak, FastAPI har bir so'rovda tokenni tekshirib, foydalanuvchini qo'limizga beradi. Agar token xato bo'lsa, funksiya ishlamay, darhol 401 qaytariladi.

---

## 6. JWT (JSON Web Token) Qanday Ishlaydi?

JWT — bu foydalanuvchini serverda sessiya ochmasdan tanib olish (stateless authentication) usulidir.
1. Foydalanuvchi login va parolini yuboradi.
2. Server tekshiradi va foydalanuvchi ID si hamda amal qilish muddatini maxfiy kalit (`JWT_SECRET_KEY`) bilan raqamli imzolaydi.
3. Server mijozga token beradi: `eyJhbGciOi...`
4. Mijoz har bir keyingi so'rovda bu tokenni `Authorization: Bearer <token>` ko'rinishida yuboradi.
5. Server kalit yordamida imzoni tekshiradi. Token buzilmagan bo'lsa, foydalanuvchi qabul qilinadi.

---

## 7. Parol Xeshlash (Password Hashing) nima?

Parollarni bazada ochiq matn (`12345678`) holida saqlash mutlaqo taqiqlanadi. Chunki baza o'g'irlansa, barcha foydalanuvchilar paroli oshkor bo'ladi.
- **Xeshlash** — bu bir tomonlama matematik o'zgartirishdir. Paroldan xesh hosil qilib bo'ladi, lekin xeshdan parolni qaytarib bo'lmaydi.
- Loyihamizda eng xavfsiz zamonaviy standart — **Argon2** ishlatilgan.
- Tekshirish vaqtida yangi kiritilgan parol xeshlanib, bazadagi xesh bilan solishtiriladi (`verify_password`).

---

## 8. Migratsiya (Alembic) nima?

Ma'lumotlar bazasida jadvallar va ustunlar vaqt o'tishi bilan o'zgaradi (masalan, yangi ustun qo'shiladi).
- **Alembic migratsiyasi** — bu ma'lumotlar bazasi tuzilishining "Git tarixi" dir.
- U jadvallarni bazadagi mavjud ma'lumotlarni o'chirib yubormasdan xavfsiz yangilash (`upgrade`) yoki orqaga qaytarish (`downgrade`) imkonini beradi.

---

## 9. Tranzaksiya va `SELECT ... FOR UPDATE` Nima Uchun Kerak?

Ombor tizimlarida eng xavfli holat — bu **Race Condition** (poyga holati).
Tasavvur qiling: Omborda **1 dona** telefon qoldi. Bir vaqtning o'zida ikkita xaridor uni sotib olishga bosdi.
- Agar oddiy `SELECT` ishlatilsa: ikkala so'rov ham "Qoldiq 1 ta ekan" deb o'qiydi va ikkalasi ham 1 tadan ayirib, qoldiqni **-1** qilib qo'yadi!

**Yechim: `SELECT ... FOR UPDATE` (Row Locking):**
1. Birinchi so'rov keladi va mahsulot qatorini qulflaydi (`FOR UPDATE`).
2. Ikkinchi so'rov birinchi so'rov tranzaksiyani tugatmaguncha **kutib turadi**.
3. Birinchi so'rov qoldiqni 0 qiladi va saqlaydi (`commit`).
4. Qulf ochiladi. Ikkinchi so'rov endi yangilangan qoldiqni (0) ko'radi va unga "Qoldiq yetarli emas" deb **409 Conflict** beriladi!
Shu sababli hech qachon omborda manfiy qoldiq paydo bo'lmaydi.

---

## 10. So'rov Qanday Qilib Routerdan Bazagacha Boradi?

Foydalanuvchi `POST /products/5/stock-in` yuborgandagi to'liq yo'l:
1. **Tarmoq / Nginx:** So'rovni qabul qilib, Uvicorn serveriga yo'naltiradi.
2. **FastAPI & Router (`routers/products.py`):** URL va metodni taniydi.
3. **Pydantic Sxema (`schemas/stock_movement.py`):** Yuborilgan JSON ni tekshiradi (miqdor musbatmi, sabab bo'shmi).
4. **Dependency (`dependencies.py`):** JWT tokenni tekshiradi, foydalanuvchi `staff` yoki `admin` ekanini tasdiqlaydi.
5. **Service (`services/stock_service.py`):** Tranzaksiya ochadi, mahsulotni qulflaydi, qoldiqni oshiradi, tarix yaratadi.
6. **SQLAlchemy & PostgreSQL (`database.py`):** SQL buyruqlarini bazaga yuboradi va bitta `commit` bilan saqlaydi.
7. **Javob:** Yangilangan qoldiq va harakat ma'lumotlari JSON ko'rinishida foydalanuvchiga qaytariladi.

---

## 11. CI va CD Farqi Nima?

- **CI (Continuous Integration):** Dasturchi kodni GitHub ga yuklaganda (push yoki pull request), avtomatik serverda testlar, xatolar va formatlash tekshiriladi. Maqsad — yaroqsiz yoki xatoli kod loyihaga qo'shilib ketmasligi.
- **CD (Continuous Deployment):** Barcha testlar muvaffaqiyatli o'tgach, yangi kod avtomatik ravishda haqiqiy ishchi serverga (AWS EC2) o'rnatiladi va server qayta ishga tushiriladi.

---

## 12. Nginx va systemd Vazifasi Nima?

- **systemd:** Linux operatsion tizimining xizmatlar boshqaruvchisidir. U bizning FastAPI ilovamizni orqa fonda (background daemon) doimiy ishlab turishini ta'minlaydi. Agar ilova tasodifan to'xtab qolsa, systemd uni darhol avtomatik qayta ishga tushiradi (`Restart=always`).
- **Nginx:** Bu veb-server va Reverse Proxy dir. U tashqi internetdan keladigan barcha so'rovlarni (port 80 / 443) qabul qiladi, xavfsizlikni ta'minlaydi, SSL sertifikatlarini boshqaradi va so'rovlarni ichki Uvicorn ilovasiga (127.0.0.1:8000) uzatadi.
