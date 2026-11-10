import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy import func
from .database import get_db
from . import models
from .dependencies import super_admin
from .models_enterprise import AuditLog
from .security import hash_password
from .notifications import send_workspace_suspension_email

router = APIRouter(prefix="/api/admin", tags=["Super Admin"])


class CompanyAdminIn(BaseModel):
    company_id: int
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


@router.post("/company-admins", status_code=201)
def create_company_admin(
    data: CompanyAdminIn,
    admin: models.User = Depends(super_admin),
    db: Session = Depends(get_db),
):
    company = db.query(models.Company).filter(models.Company.id == data.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    if not company.is_active:
        raise HTTPException(status_code=409, detail="Cannot create an administrator for an inactive company")
    if not re.search(r"[A-Z]", data.password) or not re.search(r"[a-z]", data.password) \
            or not re.search(r"\d", data.password) or not re.search(r"[^A-Za-z0-9]", data.password):
        raise HTTPException(
            status_code=422,
            detail="Password must include uppercase, lowercase, number, and special character",
        )
    email = str(data.email).lower()
    if db.query(models.User).filter(models.User.email == email).first():
        raise HTTPException(status_code=409, detail="Email is already registered")
    account = models.User(
        company_id=company.id,
        full_name=data.full_name.strip(),
        email=email,
        password_hash=hash_password(data.password),
        role="owner",
        is_active=True,
        is_email_verified=True,
        is_phone_verified=False,
        auth_provider="password",
    )
    db.add(account)
    db.flush()
    db.add(AuditLog(
        company_id=company.id,
        user_id=admin.id,
        action="create",
        resource="company_admin",
        resource_id=str(account.id),
        details=f"Created company administrator for company {company.id}",
    ))
    db.commit()
    return {
        "id": account.id,
        "company_id": account.company_id,
        "full_name": account.full_name,
        "email": account.email,
        "role": "owner",
        "message": "Company administrator created and can sign in immediately.",
    }

@router.get("/overview")
def overview(admin: models.User = Depends(super_admin), db: Session = Depends(get_db)):
    return {
        "admin": admin.email,
        "companies": db.query(func.count(models.Company.id)).scalar() or 0,
        "users": db.query(func.count(models.User.id)).scalar() or 0,
        "verified_users": db.query(func.count(models.User.id)).filter(models.User.is_email_verified.is_(True)).scalar() or 0,
        "sales_records": db.query(func.count(models.Sale.id)).scalar() or 0
    }

@router.get("/companies")
def companies(admin: models.User = Depends(super_admin), db: Session = Depends(get_db)):
    rows = db.query(models.Company).order_by(models.Company.created_at.desc()).all()
    return [{"id": c.id, "name": c.name, "industry": c.industry, "is_active": c.is_active, "deleted": c.deleted_at is not None, "created_at": c.created_at} for c in rows]


@router.get("/users")
def users(admin: models.User = Depends(super_admin), db: Session = Depends(get_db)):
    rows = db.query(models.User).order_by(models.User.created_at.desc()).limit(500).all()
    return [
        {
            "id": user.id,
            "company_id": user.company_id,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "is_email_verified": user.is_email_verified,
            "created_at": user.created_at,
        }
        for user in rows
    ]


@router.get("/audit-logs")
def audit_logs(admin: models.User = Depends(super_admin), db: Session = Depends(get_db)):
    return db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(200).all()

@router.patch("/companies/{company_id}/status")
def update_company_status(company_id: int, active: bool, admin: models.User = Depends(super_admin), db: Session = Depends(get_db)):
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Company not found")
    was_active = company.is_active
    company.is_active = active
    recipients = []
    if was_active and not active:
        recipients = db.query(models.User).filter(
            models.User.company_id == company.id,
            models.User.is_active.is_(True),
            models.User.email.is_not(None),
        ).all()
    db.commit()
    notification_failures = 0
    if was_active and not active:
        for recipient in recipients:
            try:
                send_workspace_suspension_email(
                    recipient.email,
                    company.name,
                    recipient.full_name,
                )
            except Exception:
                notification_failures += 1
    return {
        "success": True,
        "company_id": company.id,
        "is_active": company.is_active,
        "notification": {
            "attempted": len(recipients),
            "failed": notification_failures,
            "message": (
                "Suspension email notifications sent."
                if notification_failures == 0
                else f"{notification_failures} suspension email notification(s) failed; check SMTP configuration."
            ),
        },
    }


@router.delete("/companies/{company_id}")
def delete_company(
    company_id: int,
    admin: models.User = Depends(super_admin),
    db: Session = Depends(get_db),
):
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    if company.deleted_at is None:
        from datetime import datetime
        company.deleted_at = datetime.utcnow()
        company.deleted_by = admin.id
        company.is_active = False
        db.commit()
    return {"success": True, "company_id": company.id, "deleted": True}


@router.post("/companies/{company_id}/restore")
def restore_company(
    company_id: int,
    admin: models.User = Depends(super_admin),
    db: Session = Depends(get_db),
):
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    company.deleted_at = None
    company.deleted_by = None
    company.is_active = True
    db.commit()
    return {"success": True, "company_id": company.id, "deleted": False, "is_active": True}
