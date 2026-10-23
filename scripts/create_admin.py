import getpass
import sys

from app.database import SessionLocal
from app.models.user import User
from app.security import hash_password


def main():
    """Serverda yangi admin foydalanuvchini xavfsiz yaratish skripti."""
    print("=== Yangi Admin Foydalanuvchi Yaratish ===")
    email = input("Admin email manzili: ").strip().lower()

    if not email or "@" not in email:
        print("Xatolik: To'g'ri email manzili kiriting!", file=sys.stderr)
        sys.exit(1)

    password = getpass.getpass("Admin paroli (kamida 8 belgi): ")
    if len(password) < 8:
        print("Xatolik: Parol kamida 8 ta belgidan iborat bo'lishi shart!", file=sys.stderr)
        sys.exit(1)

    password_confirm = getpass.getpass("Parolni tasdiqlang: ")
    if password != password_confirm:
        print("Xatolik: Kiritilgan parollar mos kelmadi!", file=sys.stderr)
        sys.exit(1)

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"Xatolik: '{email}' emaili bilan foydalanuvchi allaqachon mavjud!", file=sys.stderr)
            sys.exit(1)

        admin_user = User(
            email=email,
            password_hash=hash_password(password),
            role="admin",
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        print(f"Muvaffaqiyatli! Admin ID: {admin_user.id}, Email: {admin_user.email}, Role: {admin_user.role}")
    except Exception as e:
        db.rollback()
        print(f"Bazada xatolik yuz berdi: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
