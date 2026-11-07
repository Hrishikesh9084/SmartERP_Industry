from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from .database import get_db
from . import models
from .dependencies import company_user

router = APIRouter(prefix="/api/ai", tags=["AI & Data Science"])

@router.get("/overview")
def ai_overview(user: models.User = Depends(company_user), db: Session = Depends(get_db)):
    cid = user.company_id
    sales_count = db.query(func.count(models.Sale.id)).filter(models.Sale.company_id == cid).scalar() or 0
    total_sales = db.query(func.coalesce(func.sum(models.Sale.amount), 0)).filter(models.Sale.company_id == cid).scalar() or 0
    product_count = db.query(func.count(models.Product.id)).filter(models.Product.company_id == cid).scalar() or 0
    customer_count = db.query(func.count(models.Customer.id)).filter(models.Customer.company_id == cid).scalar() or 0
    return {"status": "ready", "data_quality": {"sales_records": sales_count, "products": product_count, "customers": customer_count},
            "metrics": {"total_sales": round(float(total_sales), 2)},
            "message": "Models analyze only the authenticated company's data."}

@router.get("/sales-forecast")
def sales_forecast(periods: int = Query(3, ge=1, le=12), user: models.User = Depends(company_user), db: Session = Depends(get_db)):
    # Aggregate in Python so the same code works with SQLite and PostgreSQL.
    sales = db.query(models.Sale).filter(
        models.Sale.company_id == user.company_id
    ).order_by(models.Sale.created_at.asc()).all()
    monthly_totals = {}
    for sale in sales:
        key = sale.created_at.strftime("%Y-%m")
        monthly_totals[key] = monthly_totals.get(key, 0.0) + float(sale.amount)
    if len(monthly_totals) < 3:
        return {"status": "insufficient_data", "required_months": 3,
                "available_months": len(monthly_totals), "forecast": [],
                "message": "Record sales across at least 3 distinct months to create a basic forecast."}
    df = pd.DataFrame(
        [{"month": month, "sales": amount} for month, amount in sorted(monthly_totals.items())]
    )
    x = np.arange(len(df)).reshape(-1, 1)
    y = df["sales"].to_numpy()
    model = LinearRegression().fit(x, y)
    forecast = []
    for i in range(periods):
        pred = max(0.0, float(model.predict(np.array([[len(df) + i]]))[0]))
        forecast.append({"period_number": i + 1, "predicted_sales": round(pred, 2)})
    return {"status": "ok", "method": "LinearRegression", "historical_months": len(df),
            "forecast": forecast,
            "caveat": "Baseline trend estimate, not a guarantee. Add seasonality and more history for stronger forecasts."}

@router.get("/inventory-recommendations")
def inventory_recommendations(user: models.User = Depends(company_user), db: Session = Depends(get_db)):
    products = db.query(models.Product).filter(models.Product.company_id == user.company_id).all()
    result = []
    for p in products:
        if p.quantity <= p.reorder_level:
            result.append({"product_id": p.id, "name": p.name, "sku": p.sku, "available": p.quantity,
                           "reorder_level": p.reorder_level, "suggested_action": "Review and reorder"})
    return {"status": "ok", "low_stock_count": len(result), "recommendations": result}

@router.get("/customer-segments")
def customer_segments(user: models.User = Depends(company_user), db: Session = Depends(get_db)):
    customers = db.query(models.Customer).filter(models.Customer.company_id == user.company_id).all()
    if len(customers) < 3:
        return {"status": "insufficient_data", "required_customers": 3, "available_customers": len(customers), "segments": []}
    values = np.array([[max(0.0, c.total_spend)] for c in customers])
    labels = KMeans(n_clusters=min(3, len(customers)), random_state=42, n_init=10).fit_predict(values)
    result = []
    for c, label in zip(customers, labels):
        result.append({"customer_id": c.id, "name": c.name, "total_spend": c.total_spend, "segment": int(label)})
    return {"status": "ok", "method": "KMeans", "segments": result,
            "note": "Cluster numbers are labels, not ranked customer tiers."}

@router.get("/anomaly-review")
def anomaly_review(user: models.User = Depends(company_user), db: Session = Depends(get_db)):
    rows = db.query(models.Expense).filter(models.Expense.company_id == user.company_id).order_by(models.Expense.created_at.asc()).all()
    if len(rows) < 5:
        return {"status": "insufficient_data", "required_records": 5, "available_records": len(rows), "flagged": []}
    amounts = np.array([[r.amount] for r in rows])
    labels = IsolationForest(contamination=0.1, random_state=42).fit_predict(amounts)
    flagged = [{"expense_id": r.id, "amount": r.amount, "category": r.category, "description": r.description,
                "review_required": True} for r, label in zip(rows, labels) if label == -1]
    return {"status": "ok", "method": "IsolationForest", "flagged": flagged,
            "warning": "Flags are statistical outliers and do not prove fraud."}
