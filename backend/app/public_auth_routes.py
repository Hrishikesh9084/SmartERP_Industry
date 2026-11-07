from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from .config import DEV_SHOW_OTP, OTP_EXPIRY_MINUTES
from .database import get_db
from .dependencies import current_user
from .models import Company, User
from .models_enterprise import EmailOTP, PhoneOTP
from .notifications import send_email, send_sms
from .schemas import LoginIn, RegisterIn
from .security import (
    create_token,
    hash_password,
    new_otp,
    otp_digest,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class OTPVerifyIn(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)


class EmailRequestIn(BaseModel):
    email: EmailStr


class PhoneOTPIn(BaseModel):
    phone_number: str = Field(min_length=10, max_length=20)


class PhoneOTPVerifyIn(PhoneOTPIn):
    otp: str = Field(min_length=6, max_length=6)


def _user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "phone_number": user.phone,
        "role": user.role,
        "company_id": user.company_id,
    }


def _issue_email_otp(db: Session, user: User) -> str:
    code = new_otp()
    db.add(
        EmailOTP(
            user_id=user.id,
            code_hash=otp_digest(code),
            expires_at=datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES),
        )
    )
    db.commit()
    body = f"Your SmartERP email verification code is {code} For your security, please do not share this code with anyone. It expires in {OTP_EXPIRY_MINUTES} minutes."
    try:
        send_email(user.email, "SmartERP email verification", body)
    except Exception:
        if not DEV_SHOW_OTP:
            raise HTTPException(status_code=503, detail="Unable to send verification email")
    return code


def _issue_login_otp(db: Session, user: User) -> str:
    code = new_otp()
    db.add(
        EmailOTP(
            user_id=user.id,
            purpose="login",
            code_hash=otp_digest(code),
            expires_at=datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES),
        )
    )
    db.commit()
    body = f"Your SmartERP login code is {code} For your security, please do not share this code with anyone. It expires in {OTP_EXPIRY_MINUTES} minutes."
    try:
        send_email(user.email, "SmartERP login verification", body)
    except Exception:
        if not DEV_SHOW_OTP:
            raise HTTPException(status_code=503, detail="Unable to send login OTP")
    return code


def _issue_phone_otp(db: Session, user: User) -> str:
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
    if DEV_SHOW_OTP:
        return code
    try:
        if not send_sms(user.phone or "", f"SmartERP verification code: {code}"):
            raise HTTPException(status_code=503, detail="Unable to send phone verification code")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=503, detail="Unable to send phone verification code")
    return code


@router.post("/register", status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    email = str(data.email).lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="Email is already registered")
    if data.phone and db.query(User).filter(User.phone == data.phone).first():
        raise HTTPException(status_code=409, detail="Phone number is already registered")

    company = Company(name=data.company_name.strip(), industry=data.industry.strip() or "General")
    db.add(company)
    db.flush()
    user = User(
        company_id=company.id,
        full_name=data.full_name.strip(),
        email=email,
        phone=data.phone.strip() if data.phone else None,
        password_hash=hash_password(data.password),
        role="owner",
        is_active=False,
        is_email_verified=False,
        is_phone_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    code = _issue_email_otp(db, user)
    response = {"success": True, "message": "Verification OTP sent to your email."}
    if DEV_SHOW_OTP:
        response["otp"] = code
    return response


@router.post("/verify-email")
def verify_email(data: OTPVerifyIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == str(data.email).lower()).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or OTP")
    row = (
        db.query(EmailOTP)
        .filter_by(user_id=user.id, purpose="email_verification", consumed=False)
        .order_by(EmailOTP.id.desc())
        .first()
    )
    if not row or row.expires_at < datetime.utcnow() or row.attempts >= 5:
        raise HTTPException(status_code=400, detail="OTP invalid, expired or locked")
    row.attempts += 1
    if row.code_hash != otp_digest(data.otp):
        db.commit()
        raise HTTPException(status_code=400, detail="Invalid OTP")
    row.consumed = True
    user.is_email_verified = True
    db.commit()
    return {"success": True, "message": "Email verified successfully."}


@router.post("/resend-verification")
def resend_verification(data: EmailRequestIn, db: Session = Depends(get_db)):
    email = str(data.email).lower()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Account not found")
    if user.is_email_verified:
        raise HTTPException(status_code=409, detail="Email is already verified")
    code = _issue_email_otp(db, user)
    response = {"success": True, "message": "Verification OTP resent."}
    if DEV_SHOW_OTP:
        response["otp"] = code
    return response


@router.post("/request-login-otp")
def request_login_otp(data: EmailRequestIn, db: Session = Depends(get_db)):
    email = str(data.email).lower()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Account not found")
    if not user.is_email_verified:
        raise HTTPException(status_code=403, detail="Please verify your email first")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Your account is inactive")
    code = _issue_login_otp(db, user)
    response = {"success": True, "message": "Email login OTP sent successfully."}
    if DEV_SHOW_OTP:
        response["otp"] = code
    return response


@router.post("/verify-login-otp")
def verify_login_otp(data: OTPVerifyIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == str(data.email).lower()).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or OTP")
    row = (
        db.query(EmailOTP)
        .filter_by(user_id=user.id, purpose="login", consumed=False)
        .order_by(EmailOTP.id.desc())
        .first()
    )
    if not row or row.expires_at < datetime.utcnow() or row.attempts >= 5:
        raise HTTPException(status_code=400, detail="OTP invalid, expired or locked")
    row.attempts += 1
    if row.code_hash != otp_digest(data.otp):
        db.commit()
        raise HTTPException(status_code=400, detail="Invalid OTP")
    row.consumed = True
    db.commit()
    token = create_token(user.id, user.company_id, user.role)
    return {"success": True, "access_token": token, "token_type": "bearer", "user": _user_payload(user)}


@router.post("/phone/send-otp")
def send_registration_phone_otp(data: PhoneOTPIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == data.phone_number.strip()).first()
    if not user or not user.is_email_verified:
        raise HTTPException(status_code=400, detail="Verify your email before verifying your phone")
    code = _issue_phone_otp(db, user)
    response = {"success": True, "message": "Mobile OTP sent successfully."}
    if DEV_SHOW_OTP:
        response["otp"] = code
    return response


@router.post("/phone/verify-otp")
def verify_registration_phone_otp(data: PhoneOTPVerifyIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == data.phone_number.strip()).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid phone number or OTP")
    row = db.query(PhoneOTP).filter_by(user_id=user.id, consumed=False).order_by(PhoneOTP.id.desc()).first()
    if not row or row.expires_at < datetime.utcnow() or row.attempts >= 5:
        raise HTTPException(status_code=400, detail="OTP invalid, expired or locked")
    row.attempts += 1
    if row.code_hash != otp_digest(data.otp):
        db.commit()
        raise HTTPException(status_code=400, detail="Invalid OTP")
    row.consumed = True
    user.is_phone_verified = True
    user.is_active = True
    db.commit()
    return {"success": True, "message": "Phone verified successfully."}


@router.post("/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == str(data.email).lower()).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Please complete account verification first")
    token = create_token(user.id, user.company_id, user.role)
    return {"access_token": token, "token_type": "bearer", "user": _user_payload(user)}


@router.get("/me")
def me(user: User = Depends(current_user)):
    return _user_payload(user)
