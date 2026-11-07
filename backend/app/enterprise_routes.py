from datetime import datetime, timedelta
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import func
from .database import get_db
from .dependencies import company_user, current_user
from .models import User, Product
from .models_enterprise import (Employee, Attendance, LeaveRequest, PayrollRun, Payslip, Account, JournalEntry, JournalLine, Supplier, PurchaseOrder, PurchaseOrderLine, RolePermission, PhoneOTP, AuditLog)
from .permissions import require_permission
from .security import new_otp, otp_digest
from .notifications import send_sms
from .rate_limit import enforce_rate_limit, client_key
from .config import OTP_EXPIRY_MINUTES

router=APIRouter(prefix='/api',tags=['Enterprise ERP'])
class EmployeeIn(BaseModel):
    employee_code:str; first_name:str; last_name:str; email:EmailStr; phone:str|None=None; department:str='General'; designation:str='Employee'; employment_type:str='full_time'; annual_ctc:Decimal=Decimal('0')
class AttendanceIn(BaseModel): employee_id:int; work_date:datetime; status:str='present'; check_in:datetime|None=None; check_out:datetime|None=None; notes:str|None=None
class LeaveIn(BaseModel): employee_id:int; start_date:datetime; end_date:datetime; leave_type:str; reason:str
class LeaveDecision(BaseModel): status:str=Field(pattern='^(approved|rejected)$')
class PayrollIn(BaseModel): period:str=Field(pattern=r'^\d{4}-(0[1-9]|1[0-2])$'); allowance_rate:Decimal=Decimal('0'); deduction_rate:Decimal=Decimal('0')
class AccountIn(BaseModel): code:str; name:str; account_type:str=Field(pattern='^(asset|liability|equity|revenue|expense)$')
class JournalLineIn(BaseModel): account_id:int; debit:Decimal=Decimal('0'); credit:Decimal=Decimal('0'); memo:str|None=None
class JournalIn(BaseModel): description:str; reference:str|None=None; entry_date:datetime|None=None; lines:list[JournalLineIn]
class SupplierIn(BaseModel): name:str; email:EmailStr|None=None; phone:str|None=None; tax_id:str|None=None; address:str|None=None
class POLineIn(BaseModel): product_id:int; quantity:int=Field(gt=0); unit_cost:Decimal=Field(gt=0)
class PurchaseIn(BaseModel): supplier_id:int; po_number:str; lines:list[POLineIn]
class PermissionIn(BaseModel): role:str; permission:str; allowed:bool=True
class PhoneVerifyIn(BaseModel): otp:str=Field(min_length=6,max_length=6)

@router.post('/hr/employees',status_code=201)
def create_employee(data:EmployeeIn,user:User=Depends(require_permission('hr.employees.write')),db:Session=Depends(get_db)):
    item=Employee(company_id=user.company_id,**data.model_dump()); db.add(item); db.commit(); db.refresh(item); return item
@router.get('/hr/employees')
def employees(user:User=Depends(require_permission('hr.employees.read')),db:Session=Depends(get_db)):
    return db.query(Employee).filter_by(company_id=user.company_id).order_by(Employee.id.desc()).all()
@router.post('/hr/attendance',status_code=201)
def attendance(data:AttendanceIn,user:User=Depends(require_permission('hr.attendance.write')),db:Session=Depends(get_db)):
    emp=db.query(Employee).filter_by(id=data.employee_id,company_id=user.company_id).first()
    if not emp: raise HTTPException(404,'Employee not found')
    row=Attendance(company_id=user.company_id,**data.model_dump()); db.add(row); db.commit(); db.refresh(row); return row
@router.get('/hr/attendance')
def attendance_list(user:User=Depends(require_permission('hr.attendance.read')),db:Session=Depends(get_db)):
    return db.query(Attendance).filter_by(company_id=user.company_id).order_by(Attendance.work_date.desc()).limit(500).all()
@router.post('/hr/leaves',status_code=201)
def leave_request(data:LeaveIn,user:User=Depends(require_permission('hr.leave.write')),db:Session=Depends(get_db)):
    emp=db.query(Employee).filter_by(id=data.employee_id,company_id=user.company_id).first()
    if not emp or data.end_date < data.start_date: raise HTTPException(400,'Invalid employee or date range')
    row=LeaveRequest(company_id=user.company_id,**data.model_dump()); db.add(row); db.commit(); db.refresh(row); return row
@router.get('/hr/leaves')
def leaves(user:User=Depends(require_permission('hr.leave.read')),db:Session=Depends(get_db)):
    return db.query(LeaveRequest).filter_by(company_id=user.company_id).order_by(LeaveRequest.id.desc()).all()
@router.patch('/hr/leaves/{leave_id}')
def decide_leave(leave_id:int,data:LeaveDecision,user:User=Depends(require_permission('hr.leave.approve')),db:Session=Depends(get_db)):
    row=db.query(LeaveRequest).filter_by(id=leave_id,company_id=user.company_id).first()
    if not row: raise HTTPException(404,'Leave request not found')
    row.status=data.status; row.reviewed_by=user.id; db.commit(); return row
@router.post('/hr/payroll/runs',status_code=201)
def run_payroll(data:PayrollIn,user:User=Depends(require_permission('payroll.run')),db:Session=Depends(get_db)):
    if db.query(PayrollRun).filter_by(company_id=user.company_id,period=data.period).first(): raise HTTPException(409,'Payroll already exists for this period')
    staff=db.query(Employee).filter_by(company_id=user.company_id,is_active=True).all()
    if not staff: raise HTTPException(400,'Add active employees before running payroll')
    run=PayrollRun(company_id=user.company_id,period=data.period,status='draft'); db.add(run); db.flush()
    gross_total=Decimal('0'); deduction_total=Decimal('0')
    for emp in staff:
        monthly=Decimal(str(emp.annual_ctc))/Decimal('12'); basic=monthly*Decimal('0.5'); allowances=monthly-basic+data.allowance_rate
        deductions=data.deduction_rate; net=basic+allowances-deductions
        if net < 0: raise HTTPException(400,f'Payroll deductions exceed pay for {emp.employee_code}')
        db.add(Payslip(company_id=user.company_id,payroll_run_id=run.id,employee_id=emp.id,basic=basic,allowances=allowances,deductions=deductions,net_pay=net))
        gross_total+=basic+allowances; deduction_total+=deductions
    run.gross_total=gross_total; run.deduction_total=deduction_total; run.net_total=gross_total-deduction_total; run.status='calculated'; db.commit(); db.refresh(run); return run
@router.get('/hr/payroll/runs')
def payroll_runs(user:User=Depends(require_permission('payroll.read')),db:Session=Depends(get_db)):
    return db.query(PayrollRun).filter_by(company_id=user.company_id).order_by(PayrollRun.id.desc()).all()
@router.get('/hr/payroll/runs/{run_id}/payslips')
def payslips(run_id:int,user:User=Depends(require_permission('payroll.read')),db:Session=Depends(get_db)):
    run=db.query(PayrollRun).filter_by(id=run_id,company_id=user.company_id).first()
    if not run: raise HTTPException(404,'Payroll run not found')
    return db.query(Payslip).filter_by(payroll_run_id=run_id,company_id=user.company_id).all()

@router.post('/accounting/accounts',status_code=201)
def create_account(data:AccountIn,user:User=Depends(require_permission('accounting.accounts.write')),db:Session=Depends(get_db)):
    row=Account(company_id=user.company_id,**data.model_dump()); db.add(row); db.commit(); db.refresh(row); return row
@router.get('/accounting/accounts')
def accounts(user:User=Depends(require_permission('accounting.read')),db:Session=Depends(get_db)):
    return db.query(Account).filter_by(company_id=user.company_id,is_active=True).order_by(Account.code).all()
@router.post('/accounting/journals',status_code=201)
def create_journal(data:JournalIn,user:User=Depends(require_permission('accounting.journals.write')),db:Session=Depends(get_db)):
    if len(data.lines)<2: raise HTTPException(400,'A journal requires at least two lines')
    debit=sum((x.debit for x in data.lines),Decimal('0')); credit=sum((x.credit for x in data.lines),Decimal('0'))
    if debit<=0 or debit!=credit: raise HTTPException(400,'Journal must balance: total debit must equal total credit and be positive')
    ids={x.account_id for x in data.lines}; valid=db.query(Account).filter(Account.company_id==user.company_id,Account.id.in_(ids),Account.is_active.is_(True)).all()
    if len(valid)!=len(ids): raise HTTPException(400,'One or more accounts are invalid for this company')
    if any(x.debit<0 or x.credit<0 or (x.debit>0 and x.credit>0) for x in data.lines): raise HTTPException(400,'Each journal line must be debit OR credit, never both')
    entry=JournalEntry(company_id=user.company_id,description=data.description,reference=data.reference,entry_date=data.entry_date or datetime.utcnow(),created_by=user.id,status='posted'); db.add(entry); db.flush()
    for line in data.lines: db.add(JournalLine(journal_entry_id=entry.id,account_id=line.account_id,debit=line.debit,credit=line.credit,memo=line.memo))
    db.add(AuditLog(company_id=user.company_id,user_id=user.id,action='journal.posted',resource='journal_entry',resource_id=str(entry.id),details=f'debit={debit};credit={credit}'))
    db.commit(); db.refresh(entry); return {'id':entry.id,'status':entry.status,'debit_total':str(debit),'credit_total':str(credit)}
@router.get('/accounting/trial-balance')
def trial_balance(user:User=Depends(require_permission('accounting.read')),db:Session=Depends(get_db)):
    rows=db.query(Account.id,Account.code,Account.name,Account.account_type,func.coalesce(func.sum(JournalLine.debit),0).label('debits'),func.coalesce(func.sum(JournalLine.credit),0).label('credits')).outerjoin(JournalLine,JournalLine.account_id==Account.id).filter(Account.company_id==user.company_id).group_by(Account.id).order_by(Account.code).all()
    result=[{'account_id':r.id,'code':r.code,'name':r.name,'type':r.account_type,'debit':str(r.debits),'credit':str(r.credits),'net':str(Decimal(str(r.debits))-Decimal(str(r.credits)))} for r in rows]
    return {'accounts':result,'total_debits':str(sum((Decimal(str(r.debits)) for r in rows),Decimal('0'))),'total_credits':str(sum((Decimal(str(r.credits)) for r in rows),Decimal('0')))}

@router.post('/purchasing/suppliers',status_code=201)
def add_supplier(data:SupplierIn,user:User=Depends(require_permission('purchasing.suppliers.write')),db:Session=Depends(get_db)):
    row=Supplier(company_id=user.company_id,**data.model_dump()); db.add(row); db.commit(); db.refresh(row); return row
@router.get('/purchasing/suppliers')
def suppliers(user:User=Depends(require_permission('purchasing.read')),db:Session=Depends(get_db)):
    return db.query(Supplier).filter_by(company_id=user.company_id).order_by(Supplier.name).all()
@router.post('/purchasing/orders',status_code=201)
def create_po(data:PurchaseIn,user:User=Depends(require_permission('purchasing.orders.write')),db:Session=Depends(get_db)):
    supplier=db.query(Supplier).filter_by(id=data.supplier_id,company_id=user.company_id,is_active=True).first()
    if not supplier or not data.lines: raise HTTPException(400,'Valid supplier and at least one line are required')
    product_ids={x.product_id for x in data.lines}; products=db.query(Product).filter(Product.company_id==user.company_id,Product.id.in_(product_ids)).all()
    if len(products)!=len(product_ids): raise HTTPException(400,'Invalid product in purchase order')
    po=PurchaseOrder(company_id=user.company_id,supplier_id=supplier.id,po_number=data.po_number,total_amount=sum((x.quantity*x.unit_cost for x in data.lines),Decimal('0'))); db.add(po); db.flush()
    for line in data.lines: db.add(PurchaseOrderLine(purchase_order_id=po.id,product_id=line.product_id,quantity=line.quantity,unit_cost=line.unit_cost,line_total=line.quantity*line.unit_cost))
    db.commit(); db.refresh(po); return po
@router.get('/purchasing/orders')
def purchase_orders(user:User=Depends(require_permission('purchasing.read')),db:Session=Depends(get_db)):
    return db.query(PurchaseOrder).filter_by(company_id=user.company_id).order_by(PurchaseOrder.id.desc()).all()
@router.post('/purchasing/orders/{po_id}/receive')
def receive_po(po_id:int,user:User=Depends(require_permission('purchasing.receive')),db:Session=Depends(get_db)):
    po=db.query(PurchaseOrder).filter_by(id=po_id,company_id=user.company_id).first()
    if not po or po.status=='received': raise HTTPException(404,'Purchase order not found or already received')
    lines=db.query(PurchaseOrderLine).filter_by(purchase_order_id=po.id).all()
    for line in lines:
        product=db.query(Product).filter_by(id=line.product_id,company_id=user.company_id).first(); product.quantity+=line.quantity
    po.status='received'; db.commit(); return {'success':True,'purchase_order':po.po_number,'status':po.status}

@router.put('/admin/permissions')
def set_permission(data:PermissionIn,user:User=Depends(require_permission('rbac.manage')),db:Session=Depends(get_db)):
    row=db.query(RolePermission).filter_by(company_id=user.company_id,role=data.role,permission=data.permission).first()
    if row: row.allowed=data.allowed
    else: row=RolePermission(company_id=user.company_id,**data.model_dump()); db.add(row)
    db.commit(); return {'role':row.role,'permission':row.permission,'allowed':row.allowed}
@router.get('/admin/permissions')
def list_permissions(user:User=Depends(require_permission('rbac.manage')),db:Session=Depends(get_db)):
    return db.query(RolePermission).filter_by(company_id=user.company_id).order_by(RolePermission.role,RolePermission.permission).all()

@router.post('/auth/phone/request-otp')
def request_phone_otp(request:Request,user:User=Depends(current_user),db:Session=Depends(get_db)):
    if not user.phone: raise HTTPException(400,'Add a phone number to your profile first')
    enforce_rate_limit(db,client_key(request,'phone-otp',str(user.id)),3,900)
    code=new_otp(); row=PhoneOTP(user_id=user.id,code_hash=otp_digest(code),expires_at=datetime.utcnow()+timedelta(minutes=OTP_EXPIRY_MINUTES)); db.add(row); db.commit()
    sent=send_sms(user.phone,f'SmartERP verification code: {code}. Expires in {OTP_EXPIRY_MINUTES} minutes.')
    if not sent: raise HTTPException(503,'SMS provider is not configured; OTP was not delivered')
    return {'success':True,'message':'Verification code sent to your phone'}
@router.post('/auth/phone/verify')
def verify_phone(data:PhoneVerifyIn,user:User=Depends(current_user),db:Session=Depends(get_db)):
    row=db.query(PhoneOTP).filter_by(user_id=user.id,consumed=False).order_by(PhoneOTP.id.desc()).first()
    if not row or row.expires_at<datetime.utcnow() or row.attempts>=5: raise HTTPException(400,'OTP invalid, expired or locked')
    row.attempts+=1
    if row.code_hash!=otp_digest(data.otp): db.commit(); raise HTTPException(400,'Invalid OTP')
    row.consumed=True; user.is_phone_verified=True; db.commit(); return {'success':True,'phone_verified':True}

class CompanyUserIn(BaseModel):
    full_name:str; email:EmailStr; password:str=Field(min_length=12); role:str=Field(pattern='^(owner|manager|employee|hr_manager|finance_manager|inventory_manager|sales_manager)$')

@router.post('/admin/users',status_code=201)
def create_company_user(data:CompanyUserIn,user:User=Depends(require_permission('rbac.manage')),db:Session=Depends(get_db)):
    from .security import hash_password
    from .auth_routes import issue_otp
    email=str(data.email).lower()
    if db.query(User).filter_by(email=email).first(): raise HTTPException(409,'Email is already registered')
    account=User(company_id=user.company_id,full_name=data.full_name,email=email,password_hash=hash_password(data.password),role=data.role,is_active=True,is_email_verified=False)
    db.add(account); db.commit(); db.refresh(account)
    issue_otp(db,account,'email_verification')
    return {'id':account.id,'email':account.email,'role':account.role,'message':'User created. Email verification OTP sent.'}

@router.post('/accounting/seed-chart-of-accounts')
def seed_chart_of_accounts(user:User=Depends(require_permission('accounting.accounts.write')),db:Session=Depends(get_db)):
    defaults=[('1000','Cash and cash equivalents','asset'),('1100','Accounts receivable','asset'),('1200','Inventory','asset'),('1500','Property and equipment','asset'),('2000','Accounts payable','liability'),('2100','Taxes payable','liability'),('3000',"Owner's equity",'equity'),('3100','Retained earnings','equity'),('4000','Sales revenue','revenue'),('4100','Other income','revenue'),('5000','Cost of goods sold','expense'),('6000','Payroll expense','expense'),('6100','Rent expense','expense'),('6200','Utilities expense','expense'),('6300','Marketing expense','expense'),('6400','General operating expense','expense')]
    existing={r.code for r in db.query(Account).filter_by(company_id=user.company_id).all()}
    created=[]
    for code,name,kind in defaults:
        if code not in existing:
            row=Account(company_id=user.company_id,code=code,name=name,account_type=kind); db.add(row); created.append(code)
    db.commit(); return {'created_account_codes':created,'message':'Default chart of accounts initialized idempotently.'}

@router.get('/accounting/journals')
def journal_list(user:User=Depends(require_permission('accounting.read')),db:Session=Depends(get_db)):
    entries=db.query(JournalEntry).filter_by(company_id=user.company_id).order_by(JournalEntry.entry_date.desc(),JournalEntry.id.desc()).limit(500).all()
    return [{'id':e.id,'date':e.entry_date,'reference':e.reference,'description':e.description,'status':e.status,'lines':[{'account_id':ln.account_id,'debit':str(ln.debit),'credit':str(ln.credit),'memo':ln.memo} for ln in db.query(JournalLine).filter_by(journal_entry_id=e.id).all()]} for e in entries]

@router.get('/accounting/accounts/{account_id}/ledger')
def account_ledger(account_id:int,user:User=Depends(require_permission('accounting.read')),db:Session=Depends(get_db)):
    account=db.query(Account).filter_by(id=account_id,company_id=user.company_id).first()
    if not account: raise HTTPException(404,'Account not found')
    rows=db.query(JournalEntry,JournalLine).join(JournalLine,JournalLine.journal_entry_id==JournalEntry.id).filter(JournalEntry.company_id==user.company_id,JournalLine.account_id==account_id,JournalEntry.status=='posted').order_by(JournalEntry.entry_date,JournalEntry.id).all()
    balance=Decimal('0'); ledger=[]
    for entry,line in rows:
        balance += Decimal(str(line.debit))-Decimal(str(line.credit))
        ledger.append({'journal_id':entry.id,'date':entry.entry_date,'description':entry.description,'reference':entry.reference,'debit':str(line.debit),'credit':str(line.credit),'running_balance':str(balance)})
    return {'account':{'id':account.id,'code':account.code,'name':account.name,'type':account.account_type},'entries':ledger,'closing_balance':str(balance)}
