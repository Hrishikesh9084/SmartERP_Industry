"""Provision the configured platform Super Admin account."""

from pathlib import Path
import re
import sys

from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import SUPERADMIN_EMAIL, SUPERADMIN_PASSWORD
from app.database import SessionLocal
from app.models import User
from app.security import hash_password


def provision() -> None:
    if not re.search(r"[A-Z]", SUPERADMIN_PASSWORD) or not re.search(r"[a-z]", SUPERADMIN_PASSWORD) \
            or not re.search(r"\d", SUPERADMIN_PASSWORD) or not re.search(r"[^A-Za-z0-9]", SUPERADMIN_PASSWORD):
        raise SystemExit(
            "SUPERADMIN_PASSWORD must include uppercase, lowercase, number, and special character."
        )

    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == SUPERADMIN_EMAIL))
        if user:
            if user.company_id is not None and user.role != "super_admin":
                raise SystemExit(
                    f"{SUPERADMIN_EMAIL} already belongs to a company account; refusing to promote it."
                )
            user.company_id = None
            user.role = "super_admin"
            user.is_active = True
            user.is_email_verified = True
            user.password_hash = hash_password(SUPERADMIN_PASSWORD)
            message = "Super Admin credentials updated."
        else:
            user = User(
                company_id=None,
                full_name="Platform Super Admin",
                email=SUPERADMIN_EMAIL,
                password_hash=hash_password(SUPERADMIN_PASSWORD),
                role="super_admin",
                is_active=True,
                is_email_verified=True,
                is_phone_verified=False,
                auth_provider="password",
            )
            db.add(user)
            message = "Super Admin account created."
        db.commit()
        print(message)
        print(f"Login email: {SUPERADMIN_EMAIL}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    provision()
