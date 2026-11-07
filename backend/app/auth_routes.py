from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request
)
from datetime import datetime, timedelta

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .database import get_db
from .models import User
from .models_enterprise import PhoneOTP
from .config import DEV_SHOW_OTP, OTP_EXPIRY_MINUTES

from .phone_verification import (
    send_phone_otp,
    verify_phone_otp
)

from .security import create_token, new_otp, otp_digest

from .rate_limit import (
    enforce_rate_limit,
    client_key
)


# Router configuration
router = APIRouter(
    prefix="/api/auth/mobile-login",
    tags=["Mobile Login"]
)


# -----------------------------------------
# REQUEST SCHEMAS
# -----------------------------------------

class PhoneLoginRequest(BaseModel):
    phone_number: str = Field(
        min_length=10,
        max_length=20
    )


class PhoneLoginVerify(BaseModel):
    phone_number: str = Field(
        min_length=10,
        max_length=20
    )

    otp: str = Field(
        min_length=6,
        max_length=8
    )


# -----------------------------------------
# SEND MOBILE LOGIN OTP
# -----------------------------------------

@router.post("/send-otp")
def send_login_otp(
    data: PhoneLoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):

    phone_number = data.phone_number.strip()

    # Rate limiting
    enforce_rate_limit(
        db,
        client_key(
            request,
            "mobile-login",
            phone_number
        ),
        5,
        900
    )

    # Find user
    user = db.query(User).filter(
        User.phone == phone_number
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="No account found with this phone number."
        )

    # Check email verification
    if not user.is_email_verified:
        raise HTTPException(
            status_code=403,
            detail="Please verify your email first."
        )

    # Check phone verification
    if not user.is_phone_verified:
        raise HTTPException(
            status_code=403,
            detail="Please verify your phone number first."
        )

    # Check account activation
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
        send_phone_otp(phone_number)
        return {"success": True, "message": "Login OTP sent successfully."}

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Unable to send OTP. Please check Twilio configuration."
        )


# -----------------------------------------
# VERIFY MOBILE LOGIN OTP
# -----------------------------------------

@router.post("/verify-otp")
def verify_login_otp(
    data: PhoneLoginVerify,
    request: Request,
    db: Session = Depends(get_db)
):

    phone_number = data.phone_number.strip()

    # Rate limiting
    enforce_rate_limit(
        db,
        client_key(
            request,
            "verify-mobile-login",
            phone_number
        ),
        8,
        900
    )

    # Find user
    user = db.query(User).filter(
        User.phone == phone_number
    ).first()

    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid phone number or OTP."
        )

    # Verify account status
    if (
        not user.is_email_verified
        or not user.is_phone_verified
        or not user.is_active
    ):
        raise HTTPException(
            status_code=403,
            detail="Account verification or activation required."
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
            approved = verify_phone_otp(phone_number, data.otp)

        if not approved:
            raise HTTPException(
                status_code=400,
                detail="Invalid or expired OTP."
            )

        # Generate JWT using existing SmartERP function
        access_token = create_token(
        user.id,
        user.company_id,
        user.role
    )   

        return {
            "success": True,
            "message": "Mobile login successful.",
            "access_token": access_token,
            "token_type": "bearer",

            "user": {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "phone_number": user.phone,
                "role": user.role,
                "company_id": user.company_id
            }
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Mobile login verification failed."
        )