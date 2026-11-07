from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import get_db
from . import models, schemas
from .dependencies import company_user
from .notifications import send_sms

router = APIRouter(prefix="/api", tags=["Business"])

@router.get("/dashboard")
def dashboard(user: models.User = Depends(company_user), db: Session = Depends(get_db)):
    cid = user.company_id
    products = db.query(models.Product).filter(models.Product.company_id == cid).count()
    customers = db.query(models.Customer).filter(models.Customer.company_id == cid).count()
    stock = sum(p.quantity for p in db.query(models.Product).filter(models.Product.company_id == cid).all())
    sales = sum(s.amount for s in db.query(models.Sale).filter(models.Sale.company_id == cid).all())
    expenses = sum(e.amount for e in db.query(models.Expense).filter(models.Expense.company_id == cid).all())
    return {"company": user.company.name, "industry": user.company.industry,
            "kpis": {"products": products, "customers": customers, "stock_units": stock,
                     "total_sales": round(sales, 2), "total_expenses": round(expenses, 2),
                     "net_operating_result": round(sales-expenses, 2)}}

@router.get("/products")
def list_products(user: models.User = Depends(company_user), db: Session = Depends(get_db)):
    return db.query(models.Product).filter(models.Product.company_id == user.company_id).order_by(models.Product.id.desc()).all()

@router.post("/products", status_code=201)
def add_product(data: schemas.ProductIn, user: models.User = Depends(company_user), db: Session = Depends(get_db)):
    exists = db.query(models.Product).filter(models.Product.company_id == user.company_id, models.Product.sku == data.sku).first()
    if exists:
        raise HTTPException(status_code=409, detail="SKU already exists in your company")
    item = models.Product(company_id=user.company_id, **data.model_dump())
    db.add(item); db.commit(); db.refresh(item)
    if user.phone:
        try: send_sms(user.phone, f"SmartERP: Product {item.name} added. Current stock: {item.quantity}.")
        except Exception: pass
    return item

@router.get("/customers")
def list_customers(user: models.User = Depends(company_user), db: Session = Depends(get_db)):
    return db.query(models.Customer).filter(models.Customer.company_id == user.company_id).order_by(models.Customer.id.desc()).all()

@router.post("/customers", status_code=201)
def add_customer(data: schemas.CustomerIn, user: models.User = Depends(company_user), db: Session = Depends(get_db)):
    item = models.Customer(company_id=user.company_id, **data.model_dump())
    db.add(item); db.commit(); db.refresh(item)
    return item

@router.post("/sales", status_code=201)
def add_sale(data: schemas.SaleIn, user: models.User = Depends(company_user), db: Session = Depends(get_db)):
    if data.customer_id:
        customer = db.query(models.Customer).filter(models.Customer.id == data.customer_id, models.Customer.company_id == user.company_id).first()
        if not customer: raise HTTPException(status_code=404, detail="Customer not found")
        customer.total_spend += data.amount
    sale = models.Sale(company_id=user.company_id, **data.model_dump())
    db.add(sale); db.commit(); db.refresh(sale)
    return sale

@router.post("/expenses", status_code=201)
def add_expense(data: schemas.ExpenseIn, user: models.User = Depends(company_user), db: Session = Depends(get_db)):
    item = models.Expense(company_id=user.company_id, **data.model_dump())
    db.add(item); db.commit(); db.refresh(item)
    return item

@router.post("/notifications/sms")
def send_test_sms(phone: str, message: str, user: models.User = Depends(company_user)):
    if not user.phone or phone != user.phone:
        raise HTTPException(status_code=403, detail="SMS can only be sent to the signed-in user's verified profile number in this starter.")
    try:
        sent = send_sms(phone, message)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"SMS provider error: {exc}")
    if not sent:
        raise HTTPException(status_code=503, detail="SMS provider is not configured")
    return {"success": True, "message": "SMS submitted to provider"}
