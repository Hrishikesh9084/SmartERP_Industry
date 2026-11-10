"""Create repeatable development data for the SmartERP dashboard and modules."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
import sys

from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import APP_ENV
from app.database import SessionLocal
from app.models import Company, Customer, Expense, Product, Sale, User
from app.models_enterprise import (
    Account,
    Attendance,
    Employee,
    JournalEntry,
    JournalLine,
    LeaveRequest,
    PurchaseOrder,
    PurchaseOrderLine,
    RolePermission,
    Supplier,
)
from app.organization_models import Branch, Department, Warehouse
from app.security import hash_password


DEMO_EMAIL = "demo@smarterp.local"
DEMO_PASSWORD = "DemoPassword123!"
DEMO_COMPANY = "SMARTERP Demo Workspace"


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_or_create(db, model, defaults=None, **filters):
    row = db.scalar(select(model).filter_by(**filters))
    if row:
        return row, False
    row = model(**filters, **(defaults or {}))
    db.add(row)
    db.flush()
    return row, True


def seed():
    if APP_ENV not in {"development", "test"}:
        raise SystemExit("Demo data is disabled unless APP_ENV is development or test.")

    db = SessionLocal()
    try:
        company, company_created = get_or_create(
            db,
            Company,
            name=DEMO_COMPANY,
            defaults={
                "industry": "Technology",
                "business_type": "Private Limited",
                "country": "India",
                "state": "Maharashtra",
                "city": "Pune",
                "gstin": "27DEMO1234F1Z5",
                "website": "https://demo.smarterp.local",
            },
        )
        user, user_created = get_or_create(
            db,
            User,
            email=DEMO_EMAIL,
            defaults={
                "company_id": company.id,
                "full_name": "Demo Administrator",
                "first_name": "Demo",
                "last_name": "Administrator",
                "password_hash": hash_password(DEMO_PASSWORD),
                "role": "owner",
                "is_active": True,
                "is_email_verified": True,
                "is_phone_verified": True,
                "phone": "+919999999999",
            },
        )
        if user.company_id != company.id:
            raise RuntimeError(f"{DEMO_EMAIL} belongs to another company; refusing to modify it.")

        branch, _ = get_or_create(
            db, Branch, company_id=company.id, code="PUNE-HQ",
            defaults={"name": "Pune Headquarters", "city": "Pune", "state": "Maharashtra"},
        )
        department, _ = get_or_create(
            db, Department, company_id=company.id, code="SALES",
            defaults={"name": "Sales"},
        )
        warehouse, _ = get_or_create(
            db, Warehouse, company_id=company.id, code="MAIN",
            defaults={"name": "Main Warehouse", "branch_id": branch.id, "address": "Pune, Maharashtra"},
        )

        products = []
        product_specs = [
            ("Cloud ERP License", "ERP-001", "Software", 42, 10, 24999),
            ("Business Analytics Pack", "ANL-002", "Software", 7, 12, 12999),
            ("Barcode Scanner", "HW-003", "Hardware", 18, 5, 4500),
            ("Thermal Printer", "HW-004", "Hardware", 3, 5, 8500),
            ("Inventory Labels", "SUP-005", "Supplies", 120, 25, 12),
        ]
        for name, sku, category, quantity, reorder_level, price in product_specs:
            product, _ = get_or_create(
                db, Product, company_id=company.id, sku=sku,
                defaults={
                    "name": name, "category": category, "quantity": quantity,
                    "reorder_level": reorder_level, "unit_price": price,
                },
            )
            products.append(product)

        customers = []
        for name, email, phone in [
            ("Acme Retail Pvt Ltd", "accounts@acmeretail.example", "+919800000001"),
            ("Northstar Distributors", "finance@northstar.example", "+919800000002"),
            ("Greenfield Foods", "hello@greenfield.example", "+919800000003"),
        ]:
            customer, _ = get_or_create(
                db, Customer, company_id=company.id, email=email,
                defaults={"name": name, "phone": phone},
            )
            customers.append(customer)

        supplier, _ = get_or_create(
            db, Supplier, company_id=company.id, name="Vertex Technology Supply",
            defaults={"email": "orders@vertex.example", "phone": "+919700000001", "tax_id": "27VERTEX1Z5"},
        )
        for index, (amount, description, days_ago, customer) in enumerate([
            (185000, "Annual ERP subscription", 12, customers[0]),
            (76000, "Hardware order", 28, customers[1]),
            (124000, "Analytics implementation", 55, customers[2]),
            (54000, "Support renewal", 84, customers[0]),
        ]):
            sale, created = get_or_create(
                db, Sale, company_id=company.id,
                description=description,
                defaults={
                    "amount": amount, "amount_paid": amount * (0.72 if index == 0 else 1),
                    "customer_id": customer.id,
                    "created_at": utcnow() - timedelta(days=days_ago),
                },
            )
            if created:
                customer.total_spend += amount

        for amount, category, description, days_ago in [
            (42000, "Payroll", "Monthly payroll", 8),
            (18000, "Marketing", "Campaign and events", 22),
            (26500, "Operations", "Office and utilities", 40),
        ]:
            get_or_create(
                db, Expense, company_id=company.id, amount=amount,
                category=category, description=description,
                defaults={"created_at": utcnow() - timedelta(days=days_ago)},
            )

        purchase, _ = get_or_create(
            db, PurchaseOrder, company_id=company.id, po_number="PO-DEMO-001",
            defaults={"supplier_id": supplier.id, "status": "pending", "total_amount": 45000},
        )
        get_or_create(
            db, PurchaseOrderLine, purchase_order_id=purchase.id, product_id=products[2].id,
            defaults={"quantity": 10, "unit_cost": 4500, "line_total": 45000},
        )

        employee, _ = get_or_create(
            db, Employee, company_id=company.id, employee_code="EMP-001",
            defaults={
                "user_id": user.id, "first_name": "Demo", "last_name": "Administrator",
                "email": DEMO_EMAIL, "phone": "+919999999999", "department": department.name,
                "designation": "Company Administrator", "annual_ctc": 1200000,
            },
        )
        get_or_create(
            db, Attendance, employee_id=employee.id,
            work_date=utcnow().replace(hour=0, minute=0, second=0, microsecond=0),
            defaults={"company_id": company.id, "status": "present"},
        )
        get_or_create(
            db, LeaveRequest, company_id=company.id, employee_id=employee.id,
            start_date=utcnow() + timedelta(days=7),
            defaults={
                "end_date": utcnow() + timedelta(days=8),
                "leave_type": "casual", "reason": "Demo approval workflow",
            },
        )

        for code, name, account_type in [
            ("1000", "Cash and cash equivalents", "asset"),
            ("1100", "Accounts receivable", "asset"),
            ("4000", "Sales revenue", "revenue"),
            ("6100", "Operating expenses", "expense"),
        ]:
            get_or_create(
                db, Account, company_id=company.id, code=code,
                defaults={"name": name, "account_type": account_type},
            )
        revenue = db.scalar(select(Account).filter_by(company_id=company.id, code="4000"))
        cash = db.scalar(select(Account).filter_by(company_id=company.id, code="1000"))
        entry, created = get_or_create(
            db, JournalEntry, company_id=company.id, reference="DEMO-OPENING",
            defaults={"description": "Demo opening revenue", "created_by": user.id},
        )
        if created:
            db.add_all([
                JournalLine(journal_entry_id=entry.id, account_id=cash.id, debit=Decimal("100000"), credit=Decimal("0")),
                JournalLine(journal_entry_id=entry.id, account_id=revenue.id, debit=Decimal("0"), credit=Decimal("100000")),
            ])

        for role in ["manager", "accountant", "inventory_manager", "sales_manager"]:
            get_or_create(
                db, RolePermission, company_id=company.id, role=role,
                permission="dashboard.read", defaults={"allowed": True},
            )
        db.commit()
        print(f"Seed complete ({'created' if company_created else 'reused'} company).")
        print(f"Developer login: {DEMO_EMAIL} / {DEMO_PASSWORD}")
        print(f"Company: {company.name} (id={company.id}); branch={branch.code}; warehouse={warehouse.code}")
        print(f"User {'created' if user_created else 'reused'}; seed is safe to run again.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
