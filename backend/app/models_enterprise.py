from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Boolean, Numeric, Text, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

class Employee(Base):
    __tablename__ = "employees"
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, unique=True)
    employee_code: Mapped[str] = mapped_column(String(40))
    first_name: Mapped[str] = mapped_column(String(80)); last_name: Mapped[str] = mapped_column(String(80))
    email: Mapped[str] = mapped_column(String(255)); phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    department: Mapped[str] = mapped_column(String(100), default="General"); designation: Mapped[str] = mapped_column(String(100), default="Employee")
    employment_type: Mapped[str] = mapped_column(String(30), default="full_time"); date_of_joining: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    annual_ctc: Mapped[float] = mapped_column(Numeric(14,2), default=0); is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__=(UniqueConstraint('company_id','employee_code',name='uq_employee_code_company'),)

class Attendance(Base):
    __tablename__="attendance"
    id: Mapped[int]=mapped_column(primary_key=True); company_id: Mapped[int]=mapped_column(ForeignKey('companies.id'),index=True)
    employee_id: Mapped[int]=mapped_column(ForeignKey('employees.id'),index=True); work_date: Mapped[datetime]=mapped_column(DateTime,index=True)
    check_in: Mapped[datetime|None]=mapped_column(DateTime,nullable=True); check_out: Mapped[datetime|None]=mapped_column(DateTime,nullable=True)
    status: Mapped[str]=mapped_column(String(20),default='present'); notes: Mapped[str|None]=mapped_column(String(255),nullable=True)
    __table_args__=(UniqueConstraint('employee_id','work_date',name='uq_attendance_employee_day'),)

class LeaveRequest(Base):
    __tablename__='leave_requests'
    id: Mapped[int]=mapped_column(primary_key=True); company_id: Mapped[int]=mapped_column(ForeignKey('companies.id'),index=True)
    employee_id: Mapped[int]=mapped_column(ForeignKey('employees.id'),index=True); start_date: Mapped[datetime]=mapped_column(DateTime)
    end_date: Mapped[datetime]=mapped_column(DateTime); leave_type: Mapped[str]=mapped_column(String(40)); reason: Mapped[str]=mapped_column(Text)
    status: Mapped[str]=mapped_column(String(20),default='pending'); reviewed_by: Mapped[int|None]=mapped_column(ForeignKey('users.id'),nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)

class PayrollRun(Base):
    __tablename__='payroll_runs'
    id: Mapped[int]=mapped_column(primary_key=True); company_id: Mapped[int]=mapped_column(ForeignKey('companies.id'),index=True)
    period: Mapped[str]=mapped_column(String(7),index=True); status: Mapped[str]=mapped_column(String(20),default='draft')
    gross_total: Mapped[float]=mapped_column(Numeric(14,2),default=0); deduction_total: Mapped[float]=mapped_column(Numeric(14,2),default=0)
    net_total: Mapped[float]=mapped_column(Numeric(14,2),default=0); created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
    __table_args__=(UniqueConstraint('company_id','period',name='uq_payroll_period_company'),)

class Payslip(Base):
    __tablename__='payslips'
    id: Mapped[int]=mapped_column(primary_key=True); company_id: Mapped[int]=mapped_column(ForeignKey('companies.id'),index=True)
    payroll_run_id: Mapped[int]=mapped_column(ForeignKey('payroll_runs.id'),index=True); employee_id: Mapped[int]=mapped_column(ForeignKey('employees.id'),index=True)
    basic: Mapped[float]=mapped_column(Numeric(14,2)); allowances: Mapped[float]=mapped_column(Numeric(14,2),default=0)
    deductions: Mapped[float]=mapped_column(Numeric(14,2),default=0); net_pay: Mapped[float]=mapped_column(Numeric(14,2))
    __table_args__=(UniqueConstraint('payroll_run_id','employee_id',name='uq_payslip_employee_run'),)

class Account(Base):
    __tablename__='accounts'
    id: Mapped[int]=mapped_column(primary_key=True); company_id: Mapped[int]=mapped_column(ForeignKey('companies.id'),index=True)
    code: Mapped[str]=mapped_column(String(20)); name: Mapped[str]=mapped_column(String(120)); account_type: Mapped[str]=mapped_column(String(20))
    is_active: Mapped[bool]=mapped_column(Boolean,default=True)
    __table_args__=(UniqueConstraint('company_id','code',name='uq_account_code_company'),)

class JournalEntry(Base):
    __tablename__='journal_entries'
    id: Mapped[int]=mapped_column(primary_key=True); company_id: Mapped[int]=mapped_column(ForeignKey('companies.id'),index=True)
    entry_date: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,index=True); reference: Mapped[str|None]=mapped_column(String(80),nullable=True)
    description: Mapped[str]=mapped_column(String(255)); status: Mapped[str]=mapped_column(String(20),default='posted')
    created_by: Mapped[int]=mapped_column(ForeignKey('users.id')); created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)

class JournalLine(Base):
    __tablename__='journal_lines'
    id: Mapped[int]=mapped_column(primary_key=True); journal_entry_id: Mapped[int]=mapped_column(ForeignKey('journal_entries.id'),index=True)
    account_id: Mapped[int]=mapped_column(ForeignKey('accounts.id'),index=True); debit: Mapped[float]=mapped_column(Numeric(14,2),default=0)
    credit: Mapped[float]=mapped_column(Numeric(14,2),default=0); memo: Mapped[str|None]=mapped_column(String(255),nullable=True)

class Supplier(Base):
    __tablename__='suppliers'
    id: Mapped[int]=mapped_column(primary_key=True); company_id: Mapped[int]=mapped_column(ForeignKey('companies.id'),index=True)
    name: Mapped[str]=mapped_column(String(160)); email: Mapped[str|None]=mapped_column(String(255),nullable=True)
    phone: Mapped[str|None]=mapped_column(String(40),nullable=True); tax_id: Mapped[str|None]=mapped_column(String(40),nullable=True)
    address: Mapped[str|None]=mapped_column(Text,nullable=True); is_active: Mapped[bool]=mapped_column(Boolean,default=True)

class PurchaseOrder(Base):
    __tablename__='purchase_orders'
    id: Mapped[int]=mapped_column(primary_key=True); company_id: Mapped[int]=mapped_column(ForeignKey('companies.id'),index=True)
    supplier_id: Mapped[int]=mapped_column(ForeignKey('suppliers.id'),index=True); po_number: Mapped[str]=mapped_column(String(40))
    order_date: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow); status: Mapped[str]=mapped_column(String(20),default='draft')
    total_amount: Mapped[float]=mapped_column(Numeric(14,2),default=0); __table_args__=(UniqueConstraint('company_id','po_number',name='uq_po_company_number'),)

class PurchaseOrderLine(Base):
    __tablename__='purchase_order_lines'
    id: Mapped[int]=mapped_column(primary_key=True); purchase_order_id: Mapped[int]=mapped_column(ForeignKey('purchase_orders.id'),index=True)
    product_id: Mapped[int]=mapped_column(ForeignKey('products.id')); quantity: Mapped[int]=mapped_column(Integer)
    unit_cost: Mapped[float]=mapped_column(Numeric(14,2)); line_total: Mapped[float]=mapped_column(Numeric(14,2))

class RolePermission(Base):
    __tablename__='role_permissions'
    id: Mapped[int]=mapped_column(primary_key=True); company_id: Mapped[int]=mapped_column(ForeignKey('companies.id'),index=True)
    role: Mapped[str]=mapped_column(String(40)); permission: Mapped[str]=mapped_column(String(100)); allowed: Mapped[bool]=mapped_column(Boolean,default=True)
    __table_args__=(UniqueConstraint('company_id','role','permission',name='uq_role_permission'),)

class PhoneOTP(Base):
    __tablename__='phone_otps'
    id: Mapped[int]=mapped_column(primary_key=True); user_id: Mapped[int]=mapped_column(ForeignKey('users.id'),index=True)
    code_hash: Mapped[str]=mapped_column(String(64)); expires_at: Mapped[datetime]=mapped_column(DateTime); attempts: Mapped[int]=mapped_column(Integer,default=0)
    consumed: Mapped[bool]=mapped_column(Boolean,default=False); created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)

class EmailOTP(Base):
    __tablename__ = "email_otps"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    code_hash: Mapped[str] = mapped_column(String(64))
    purpose: Mapped[str] = mapped_column(String(40), default="email_verification")
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    consumed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class RateLimitEvent(Base):
    __tablename__='rate_limit_events'
    id: Mapped[int]=mapped_column(primary_key=True); bucket: Mapped[str]=mapped_column(String(160),index=True); created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,index=True)

class Subscription(Base):
    __tablename__='subscriptions'
    id: Mapped[int]=mapped_column(primary_key=True); company_id: Mapped[int]=mapped_column(ForeignKey('companies.id'),index=True)
    provider: Mapped[str]=mapped_column(String(20)); provider_customer_id: Mapped[str|None]=mapped_column(String(120),nullable=True)
    provider_subscription_id: Mapped[str|None]=mapped_column(String(120),nullable=True); plan_code: Mapped[str]=mapped_column(String(40))
    status: Mapped[str]=mapped_column(String(30),default='created'); amount: Mapped[float]=mapped_column(Numeric(12,2)); currency: Mapped[str]=mapped_column(String(3),default='INR')
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)

class AuditLog(Base):
    __tablename__='audit_logs'
    id: Mapped[int]=mapped_column(primary_key=True); company_id: Mapped[int|None]=mapped_column(ForeignKey('companies.id'),nullable=True,index=True)
    user_id: Mapped[int|None]=mapped_column(ForeignKey('users.id'),nullable=True); action: Mapped[str]=mapped_column(String(100))
    resource: Mapped[str]=mapped_column(String(100)); resource_id: Mapped[str|None]=mapped_column(String(80),nullable=True)
    details: Mapped[str|None]=mapped_column(Text,nullable=True); ip_address: Mapped[str|None]=mapped_column(String(64),nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,index=True)
