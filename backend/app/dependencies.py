from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .database import get_db
from .models import User
from .security import decode_token

bearer = HTTPBearer(auto_error=False)

def current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)):
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.query(User).filter(User.id == int(payload["sub"]), User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    if user.company_id != payload.get("company_id") or user.role != payload.get("role"):
        raise HTTPException(status_code=401, detail="Session is no longer valid")
    if user.company_id is not None:
        from .models import Company
        company = db.query(Company).filter(Company.id == user.company_id).first()
        if company is None or not company.is_active:
            raise HTTPException(status_code=403, detail="Company workspace is inactive")
    return user

def company_user(user: User = Depends(current_user)):
    if user.company_id is None or user.role == "super_admin":
        raise HTTPException(status_code=403, detail="Company account required")
    return user

def super_admin(user: User = Depends(current_user)):
    if user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Super Admin access required")
    return user
