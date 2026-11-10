from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .database import get_db
from .dependencies import company_user
from .models import Company, User
from .organization_models import Branch, Department, Warehouse
from .permissions import require_permission

router = APIRouter(prefix="/api/organization", tags=["Organization"])


class CompanyUpdateIn(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    industry: str = Field(min_length=1, max_length=100)
    business_type: str = Field(min_length=1, max_length=100)
    country: str = Field(min_length=1, max_length=100)
    state: str = Field(default="", max_length=100)
    city: str = Field(default="", max_length=100)
    gstin: str | None = Field(default=None, max_length=32)
    website: str | None = Field(default=None, max_length=255)


class BranchIn(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    code: str = Field(min_length=1, max_length=40)
    address: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)


class DepartmentIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    code: str = Field(min_length=1, max_length=40)


class WarehouseIn(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    code: str = Field(min_length=1, max_length=40)
    branch_id: int | None = None
    address: str | None = Field(default=None, max_length=255)


def _company(user: User, db: Session) -> Company:
    company = db.query(Company).filter(Company.id == user.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.get("/company")
def get_company(user: User = Depends(company_user), db: Session = Depends(get_db)):
    return _company(user, db)


@router.put("/company")
def update_company(
    data: CompanyUpdateIn,
    user: User = Depends(require_permission("organization.company.write")),
    db: Session = Depends(get_db),
):
    company = _company(user, db)
    for key, value in data.model_dump().items():
        setattr(company, key, value.strip() if isinstance(value, str) else value)
    db.commit()
    db.refresh(company)
    return company


@router.get("/branches")
def list_branches(user: User = Depends(company_user), db: Session = Depends(get_db)):
    return (
        db.query(Branch)
        .filter(Branch.company_id == user.company_id)
        .order_by(Branch.name)
        .all()
    )


@router.post("/branches", status_code=201)
def create_branch(
    data: BranchIn,
    user: User = Depends(require_permission("organization.branches.write")),
    db: Session = Depends(get_db),
):
    if db.query(Branch).filter_by(company_id=user.company_id, code=data.code).first():
        raise HTTPException(status_code=409, detail="Branch code already exists")
    row = Branch(company_id=user.company_id, **data.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/departments")
def list_departments(user: User = Depends(company_user), db: Session = Depends(get_db)):
    return (
        db.query(Department)
        .filter(Department.company_id == user.company_id)
        .order_by(Department.name)
        .all()
    )


@router.post("/departments", status_code=201)
def create_department(
    data: DepartmentIn,
    user: User = Depends(require_permission("organization.departments.write")),
    db: Session = Depends(get_db),
):
    if db.query(Department).filter_by(company_id=user.company_id, code=data.code).first():
        raise HTTPException(status_code=409, detail="Department code already exists")
    row = Department(company_id=user.company_id, **data.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/warehouses")
def list_warehouses(user: User = Depends(company_user), db: Session = Depends(get_db)):
    return (
        db.query(Warehouse)
        .filter(Warehouse.company_id == user.company_id)
        .order_by(Warehouse.name)
        .all()
    )


@router.post("/warehouses", status_code=201)
def create_warehouse(
    data: WarehouseIn,
    user: User = Depends(require_permission("organization.warehouses.write")),
    db: Session = Depends(get_db),
):
    if data.branch_id and not db.query(Branch).filter_by(
        id=data.branch_id, company_id=user.company_id
    ).first():
        raise HTTPException(status_code=400, detail="Branch does not belong to this company")
    if db.query(Warehouse).filter_by(company_id=user.company_id, code=data.code).first():
        raise HTTPException(status_code=409, detail="Warehouse code already exists")
    row = Warehouse(company_id=user.company_id, **data.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
