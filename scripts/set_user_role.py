import sys

from app.database import SessionLocal
from app.models.user import User

VALID_ROLES = {"user", "staff", "admin"}


def main():
    """Foydalanuvchi rolini o'zgartirish skripti (masalan: staff yoki admin qilish)."""
    print("=== Foydalanuvchi Rolini O'zgartirish ===")
    email = input("Foydalanuvchi emaili: ").strip().lower()

    if not email:
        print("Xatolik: Email bo'sh bo'lishi mumkin emas!", file=sys.stderr)
        sys.exit(1)

    print(f"Ruxsat etilgan rollar: {', '.join(sorted(VALID_ROLES))}")
    new_role = input("Yangi rol: ").strip().lower()

    if new_role not in VALID_ROLES:
        print(
            f"Xatolik: Noto'g'ri rol! Faqat quyidagilar mumkin: {', '.join(sorted(VALID_ROLES))}",
            file=sys.stderr,
        )
        sys.exit(1)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"Xatolik: '{email}' emaili bo'yicha foydalanuvchi topilmadi!", file=sys.stderr)
            sys.exit(1)

        old_role = user.role
        user.role = new_role
        db.commit()
        print(f"Muvaffaqiyatli! Foydalanuvchi {user.email} roli '{old_role}' dan '{new_role}' ga o'zgartirildi.")
    except Exception as e:
        db.rollback()
        print(f"Bazada xatolik: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
