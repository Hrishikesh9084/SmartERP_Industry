from datetime import datetime, timedelta
import re
from urllib.parse import urlencode
import secrets
import httpx

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from .config import (
    DEV_SHOW_OTP,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    FRONTEND_ORIGIN,
    OTP_EXPIRY_MINUTES,
    SECRET_KEY,
)
from .database import get_db
from .dependencies import current_user
from .models import Company, User
from .models_enterprise import EmailOTP, PhoneOTP
from .notifications import send_otp_email
from .phone_verification import send_phone_otp, verify_phone_otp
from .schemas import LoginIn, RegisterIn
from .security import (
    create_token,
    hash_password,
    new_otp,
    otp_digest,
    verify_password,
)
from jose import jwt

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


class ResetPasswordIn(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)
    password: str = Field(min_length=8, max_length=128)


def _user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "full_name": user.full_name,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "phone_number": user.phone,
        "role": user.role,
        "company_id": user.company_id,
    }


def _validate_password(password: str) -> None:
    if (
        len(password) < 8
        or not re.search(r"[A-Z]", password)
        or not re.search(r"[a-z]", password)
        or not re.search(r"\d", password)
        or not re.search(r"[^A-Za-z0-9]", password)
    ):
        raise HTTPException(
            status_code=422,
            detail="Password must be at least 8 characters and include uppercase, lowercase, number, and special character",
        )


@router.get("/google/login")
def google_login():
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=503, detail="Google authentication is not configured")
    state = jwt.encode(
        {"nonce": secrets.token_urlsafe(24), "exp": datetime.utcnow() + timedelta(minutes=10)},
        SECRET_KEY,
        algorithm="HS256",
    )
    params = urlencode(
        {
            "client_id": GOOGLE_CLIENT_ID,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "online",
            "prompt": "select_account",
        }
    )
    from fastapi.responses import RedirectResponse
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{params}")


@router.get("/google/callback")
def google_callback(code: str, state: str, db: Session = Depends(get_db)):
    from fastapi.responses import RedirectResponse

    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=503, detail="Google authentication is not configured")
    try:
        jwt.decode(state, SECRET_KEY, algorithms=["HS256"])
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired Google OAuth state")
    try:
        token_response = httpx.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
            timeout=10,
        )
        token_response.raise_for_status()
        google_tokens = token_response.json()
        userinfo_response = httpx.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {google_tokens['access_token']}"},
            timeout=10,
        )
        userinfo_response.raise_for_status()
        profile = userinfo_response.json()
    except (httpx.HTTPError, KeyError) as exc:
        raise HTTPException(status_code=502, detail=f"Google authentication failed: {exc}")

    email = str(profile.get("email", "")).lower()
    if not email or not profile.get("email_verified"):
        raise HTTPException(status_code=400, detail="Google did not provide a verified email")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        name = (profile.get("name") or email.split("@")[0]).strip()
        company = Company(name=f"{name}'s Workspace", industry="General")
        db.add(company)
        db.flush()
        user = User(
            company_id=company.id,
            full_name=name,
            first_name=profile.get("given_name"),
            last_name=profile.get("family_name"),
            email=email,
            password_hash=hash_password(secrets.token_urlsafe(32)),
            role="owner",
            is_active=True,
            is_email_verified=True,
            is_phone_verified=False,
            auth_provider="google",
            provider_user_id=profile.get("sub"),
        )
        db.add(user)
    else:
        if user.auth_provider not in ("password", "google"):
            raise HTTPException(status_code=409, detail="This account uses another sign-in provider")
        user.auth_provider = "google"
        user.provider_user_id = profile.get("sub")
        user.is_email_verified = True
        user.is_active = True
    db.commit()
    db.refresh(user)
    token = create_token(user.id, user.company_id, user.role)
    return RedirectResponse(f"{FRONTEND_ORIGIN.split(',')[0].strip()}#oauth_token={token}")


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
    try:
        send_otp_email(user.email, code, "email_verification", user.full_name)
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
    try:
        send_otp_email(user.email, code, "login", user.full_name)
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
        send_phone_otp(user.phone or "")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=503, detail="Unable to send phone verification code")
    return code


@router.post("/register", status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    _validate_password(data.password)
    email = str(data.email).lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="Email is already registered")
    if data.phone and db.query(User).filter(User.phone == data.phone).first():
        raise HTTPException(status_code=409, detail="Phone number is already registered")

    full_name = data.full_name or f"{(data.first_name or '').strip()} {(data.last_name or '').strip()}".strip()
    if len(full_name) < 2:
        raise HTTPException(status_code=422, detail="A first and last name are required")
    company = Company(
        name=data.company_name.strip(),
        industry=data.industry.strip() or "General",
        business_type=data.business_type.strip() or "General",
        country=data.country.strip() or "India",
        state=data.state.strip(),
        city=data.city.strip(),
        gstin=data.gstin.strip() if data.gstin else None,
        website=data.website.strip() if data.website else None,
    )
    db.add(company)
    db.flush()
    user = User(
        company_id=company.id,
        full_name=full_name,
        first_name=(data.first_name or full_name.split()[0]).strip(),
        last_name=(data.last_name or (full_name.split(maxsplit=1)[1] if len(full_name.split()) > 1 else "")).strip(),
        email=email,
        phone=data.phone.strip() if data.phone else None,
        password_hash=hash_password(data.password),
        role="owner",
        is_active=False,
        is_email_verified=False,
        is_phone_verified=False,
        auth_provider="password",
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
    approved = row.code_hash == otp_digest(data.otp)
    if not approved:
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


@router.post("/forgot-password")
def forgot_password(data: EmailRequestIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == str(data.email).lower()).first()
    if user:
        code = new_otp()
        db.add(
            EmailOTP(
                user_id=user.id,
                purpose="password_reset",
                code_hash=otp_digest(code),
                expires_at=datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES),
            )
        )
        db.commit()
        try:
            send_otp_email(user.email, code, "password_reset", user.full_name)
        except Exception:
            if not DEV_SHOW_OTP:
                raise HTTPException(status_code=503, detail="Unable to send password reset email")
    response = {"success": True, "message": "If that email exists, a reset code has been sent."}
    if user and DEV_SHOW_OTP:
        response["otp"] = code
    return response


@router.post("/reset-password")
def reset_password(data: ResetPasswordIn, db: Session = Depends(get_db)):
    _validate_password(data.password)
    user = db.query(User).filter(User.email == str(data.email).lower()).first()
    row = (
        db.query(EmailOTP)
        .filter_by(user_id=user.id if user else 0, purpose="password_reset", consumed=False)
        .order_by(EmailOTP.id.desc())
        .first()
    )
    if not user or not row or row.expires_at < datetime.utcnow() or row.attempts >= 5:
        raise HTTPException(status_code=400, detail="Reset code is invalid or expired")
    row.attempts += 1
    if row.code_hash != otp_digest(data.otp):
        db.commit()
        raise HTTPException(status_code=400, detail="Reset code is invalid or expired")
    row.consumed = True
    user.password_hash = hash_password(data.password)
    db.commit()
    return {"success": True, "message": "Password reset successfully. You can now sign in."}


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
    user = db.query(User).filter(User.email == data.email.strip().lower()).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Please complete account verification first")
    token = create_token(user.id, user.company_id, user.role)
    return {"access_token": token, "token_type": "bearer", "user": _user_payload(user)}


@router.get("/me")
def me(user: User = Depends(current_user)):
    return _user_payload(user)


@router.post("/logout")
def logout():
    return {"success": True, "message": "Signed out successfully."}
