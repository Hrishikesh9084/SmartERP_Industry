import os
import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from twilio.rest import Client

from .database import get_db
from .models import User

router = APIRouter(
    prefix="/api/auth/phone",
    tags=["Phone Verification"]
)


class PhoneOTPRequest(BaseModel):
    phone_number: str = Field(min_length=10, max_length=20)


class PhoneOTPVerify(BaseModel):
    phone_number: str
    otp: str = Field(min_length=6, max_length=6)


def get_twilio_service():
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    service_sid = os.getenv("TWILIO_VERIFY_SERVICE_SID")

    if not sid or not token or not service_sid:
        raise RuntimeError("Twilio configuration missing.")

    client = Client(sid, token)

    return client.verify.v2.services(service_sid)


@router.post("/send-otp")
def send_phone_otp(
    data: PhoneOTPRequest,
    db: Session = Depends(get_db)
):
    phone = data.phone_number.strip()

    if not re.fullmatch(r"\+[1-9]\d{7,14}", phone):
        raise HTTPException(
            status_code=400,
            detail="Invalid international phone number."
        )

    user = db.query(User).filter(
        User.phone == phone
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found. Please register first."
        )

    if not user.is_email_verified:
        raise HTTPException(
            status_code=403,
            detail="Please verify your email first."
        )

    if user.is_phone_verified:
        return {"message": "Phone already verified."}

    try:
        result = get_twilio_service().verifications.create(
            to=phone,
            channel="sms"
        )

        return {
            "message": "Mobile OTP sent successfully.",
            "status": result.status
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to send mobile OTP. Check Twilio configuration."
        )


@router.post("/verify-otp")
def verify_phone_otp(
    data: PhoneOTPVerify,
    db: Session = Depends(get_db)
):
    phone = data.phone_number.strip()

    user = db.query(User).filter(
        User.phone == phone
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found."
        )

    if not user.is_email_verified:
        raise HTTPException(
            status_code=403,
            detail="Email verification required."
        )

    if user.is_phone_verified:
        return {"message": "Phone already verified."}

    try:
        result = get_twilio_service().verification_checks.create(
            to=phone,
            code=data.otp
        )

        if result.status != "approved":
            raise HTTPException(
                status_code=400,
                detail="Invalid or expired OTP."
            )

        user.is_phone_verified = True

        # Activate only after both verification steps.
        user.is_active = (
            user.is_email_verified and user.is_phone_verified
        )

        db.commit()

        return {
            "message": "Mobile number verified successfully!",
            "phone_verified": True,
            "account_active": user.is_active
        }

    except HTTPException:
        raise

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Mobile verification failed."
        )