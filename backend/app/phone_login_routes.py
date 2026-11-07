from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .database import get_db
from .models import User
from .phone_verification import (
    send_phone_otp,
    verify_phone_otp
)
from .security import create_token


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
        approved = verify_phone_otp(
            data.phone_number,
            data.otp
        )

        if not approved:
            raise HTTPException(
                status_code=400,
                detail="Invalid or expired OTP."
            )

        access_token = create_token(
            data={"sub": str(user.id)}
        )

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