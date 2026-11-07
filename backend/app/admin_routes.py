from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from .database import get_db
from . import models
from .dependencies import super_admin

router = APIRouter(prefix="/api/admin", tags=["Super Admin"])

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
    return [{"id": c.id, "name": c.name, "industry": c.industry, "is_active": c.is_active, "created_at": c.created_at} for c in rows]

@router.patch("/companies/{company_id}/status")
def update_company_status(company_id: int, active: bool, admin: models.User = Depends(super_admin), db: Session = Depends(get_db)):
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Company not found")
    company.is_active = active
    db.commit()
    return {"success": True, "company_id": company.id, "is_active": company.is_active}
