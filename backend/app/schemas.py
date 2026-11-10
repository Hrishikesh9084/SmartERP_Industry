from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class RegisterIn(BaseModel):
    company_name: str = Field(min_length=2, max_length=160)
    industry: str = Field(default="General", max_length=100)
    full_name: str | None = Field(default=None, max_length=120)
    first_name: str | None = Field(default=None, max_length=80)
    last_name: str | None = Field(default=None, max_length=80)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=30)
    password: str = Field(min_length=8, max_length=128)
    business_type: str = Field(default="General", max_length=100)
    country: str = Field(default="India", max_length=100)
    state: str = Field(default="", max_length=100)
    city: str = Field(default="", max_length=100)
    gstin: str | None = Field(default=None, max_length=32)
    website: str | None = Field(default=None, max_length=255)

class LoginIn(BaseModel):
    # Development seed accounts may use reserved local domains such as .local.
    email: str = Field(min_length=3, max_length=255)
    password: str

class OTPRequestIn(BaseModel):
    email: EmailStr

class OTPVerifyIn(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)

class ProductIn(BaseModel):
    name: str
    sku: str
    category: str = "General"
    quantity: int = Field(default=0, ge=0)
    reorder_level: int = Field(default=5, ge=0)
    unit_price: float = Field(default=0, ge=0)

class CustomerIn(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class SaleIn(BaseModel):
    amount: float = Field(gt=0)
    description: str = "Sale"
    customer_id: Optional[int] = None

class ExpenseIn(BaseModel):
    amount: float = Field(gt=0)
    category: str
    description: str = ""
