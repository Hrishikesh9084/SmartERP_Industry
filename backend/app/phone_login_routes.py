from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .config import DEV_SHOW_OTP, OTP_EXPIRY_MINUTES
from .database import get_db
from .models import User
from .models_enterprise import PhoneOTP
from .phone_verification import (
    send_phone_otp,
    verify_phone_otp
)
from .security import create_token, new_otp, otp_digest


router = APIRouter(
    prefix="/api/auth/mobile-login",
    tags=["Mobile Login"]
)


class PhoneLoginRequest(BaseModel):
    phone_number: str = Field(min_length=10, max_length=20)


class PhoneLoginVerify(BaseModel):
    phone_number: str = Field(min_length=10, max_length=20)
    otp: str = Field(min_length=6, max_length=8)


@router.post("/send-otp")
def send_login_otp(
    data: PhoneLoginRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.phone == data.phone_number
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="No account found with this phone number."
        )

    if not user.is_phone_verified:
        raise HTTPException(
            status_code=403,
            detail="Please verify your phone number first."
        )

    if not user.is_email_verified:
        raise HTTPException(
            status_code=403,
            detail="Please verify your email first."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Your account is inactive."
        )

    if DEV_SHOW_OTP:
        code = new_otp()
        db.add(
            PhoneOTP(
                user_id=user.id,
                code_hash=otp_digest(code),
                expires_at=datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES),
                consumed=False,
            )
        )
        db.commit()
        return {
            "success": True,
            "message": "Development mobile OTP generated.",
            "otp": code,
        }

    try:
        send_phone_otp(data.phone_number)

        return {
            "message": "Login OTP sent successfully."
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to send OTP. Please check Twilio configuration."
        )


@router.post("/verify-otp")
def verify_login_otp(
    data: PhoneLoginVerify,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.phone == data.phone_number
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Account not found."
        )

    if not user.is_phone_verified or not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Phone verification or account activation required."
        )

    try:
        if DEV_SHOW_OTP:
            row = (
                db.query(PhoneOTP)
                .filter_by(user_id=user.id, consumed=False)
                .order_by(PhoneOTP.id.desc())
                .first()
            )
            if not row or row.expires_at < datetime.utcnow() or row.attempts >= 5:
                raise HTTPException(status_code=400, detail="Invalid or expired OTP.")
            row.attempts += 1
            approved = row.code_hash == otp_digest(data.otp)
            if approved:
                row.consumed = True
            db.commit()
        else:
            approved = verify_phone_otp(data.phone_number, data.otp)

        if not approved:
            raise HTTPException(status_code=400, detail="Invalid or expired OTP.")

        access_token = create_token(user.id, user.company_id, user.role)

        return {
            "message": "Login successful.",
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "phone_number": user.phone
            }
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Login verification failed."
        )