from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class RegisterIn(BaseModel):
    company_name: str = Field(min_length=2, max_length=160)
    industry: str = "General"
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: Optional[str] = None
    password: str = Field(min_length=10, max_length=128)

class LoginIn(BaseModel):
    email: EmailStr
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
