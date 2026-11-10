from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from .database import get_db
from . import models, schemas
from .dependencies import company_user
from .notifications import send_sms
from .models_enterprise import LeaveRequest, PurchaseOrder, Supplier

router = APIRouter(prefix="/api", tags=["Business"])

@router.get("/dashboard")
def dashboard(user: models.User = Depends(company_user), db: Session = Depends(get_db)):
    cid = user.company_id
    products_query = db.query(models.Product).filter(models.Product.company_id == cid)
    sales_query = db.query(models.Sale).filter(models.Sale.company_id == cid)
    expenses_query = db.query(models.Expense).filter(models.Expense.company_id == cid)
    sales = float(sales_query.with_entities(func.coalesce(func.sum(models.Sale.amount), 0)).scalar() or 0)
    expenses = float(expenses_query.with_entities(func.coalesce(func.sum(models.Expense.amount), 0)).scalar() or 0)
    outstanding = float(
        sales_query.with_entities(
            func.coalesce(func.sum(models.Sale.amount - models.Sale.amount_paid), 0)
        ).scalar() or 0
    )
    product_rows = products_query.all()
    now = datetime.utcnow()
    month_totals = []
    for offset in range(5, -1, -1):
        month = (now.month - offset - 1) % 12 + 1
        year = now.year + ((now.month - offset - 1) // 12)
        total = sum(
            float(s.amount)
            for s in sales_query.all()
            if s.created_at and s.created_at.year == year and s.created_at.month == month
        )
        month_totals.append({"month": f"{year}-{month:02d}", "revenue": round(total, 2)})
    recent_sales = sales_query.order_by(models.Sale.created_at.desc()).limit(5).all()
    recent_expenses = expenses_query.order_by(models.Expense.created_at.desc()).limit(5).all()
    recent = [
        {"type": "sale", "description": item.description, "amount": round(float(item.amount), 2), "date": item.created_at}
        for item in recent_sales
    ] + [
        {"type": "expense", "description": item.description or item.category, "amount": round(float(item.amount), 2), "date": item.created_at}
        for item in recent_expenses
    ]
    recent.sort(key=lambda item: item["date"] or datetime.min, reverse=True)
    low_stock = [
        {"id": item.id, "name": item.name, "sku": item.sku, "quantity": item.quantity, "reorder_level": item.reorder_level}
        for item in product_rows if item.quantity <= item.reorder_level
    ]
    pending_leaves = db.query(LeaveRequest).filter(
        LeaveRequest.company_id == cid, LeaveRequest.status == "pending"
    ).count()
    pending_purchases = db.query(PurchaseOrder).filter(
        PurchaseOrder.company_id == cid, PurchaseOrder.status == "pending"
    ).count()
    return {"company": user.company.name, "industry": user.company.industry,
            "kpis": {"products": products_query.count(),
                     "customers": db.query(models.Customer).filter(models.Customer.company_id == cid).count(),
                     "suppliers": db.query(Supplier).filter(Supplier.company_id == cid).count(),
                     "stock_units": sum(p.quantity for p in product_rows),
                     "inventory_value": round(sum(p.quantity * p.unit_price for p in product_rows), 2),
                     "total_sales": round(sales, 2), "total_expenses": round(expenses, 2),
                     "net_operating_result": round(sales-expenses, 2),
                     "outstanding_payments": round(outstanding, 2)},
            "monthly_revenue": month_totals,
            "recent_transactions": recent[:8],
            "low_stock": low_stock[:10],
            "pending_approvals": {"leave_requests": pending_leaves, "purchase_orders": pending_purchases},
            "notifications": [{"type": "low_stock", "count": len(low_stock), "message": f"{len(low_stock)} products need replenishment"}] if low_stock else []}

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
