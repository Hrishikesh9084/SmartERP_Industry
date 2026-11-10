from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    industry: Mapped[str] = mapped_column(String(100), default="General")
    business_type: Mapped[str] = mapped_column(String(100), default="General")
    country: Mapped[str] = mapped_column(String(100), default="India")
    state: Mapped[str] = mapped_column(String(100), default="")
    city: Mapped[str] = mapped_column(String(100), default="")
    gstin: Mapped[str | None] = mapped_column(String(32), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    deleted_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    company_id: Mapped[int | None] = mapped_column(
        ForeignKey("companies.id"),
        nullable=True,
        index=True
    )

    full_name: Mapped[str] = mapped_column(String(120))
    first_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(80), nullable=True)

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True
    )

    phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        index=True
    )

    password_hash: Mapped[str] = mapped_column(String(255))

    role: Mapped[str] = mapped_column(
        String(30),
        default="owner",
        index=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    is_email_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    is_phone_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    auth_provider: Mapped[str] = mapped_column(String(30), default="password")
    provider_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    company = relationship(
        "Company",
        foreign_keys=[company_id]
    )
    
class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(160), index=True)
    sku: Mapped[str] = mapped_column(String(80), index=True)
    category: Mapped[str] = mapped_column(String(100), default="General")
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    reorder_level: Mapped[int] = mapped_column(Integer, default=5)
    unit_price: Mapped[float] = mapped_column(Float, default=0)


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    total_spend: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Sale(Base):
    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"), nullable=True)
    amount: Mapped[float] = mapped_column(Float)
    amount_paid: Mapped[float] = mapped_column(Float, default=0)
    description: Mapped[str] = mapped_column(String(255), default="Sale")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    amount: Mapped[float] = mapped_column(Float)
    category: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)