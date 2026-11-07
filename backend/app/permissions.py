from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from .database import get_db
from .dependencies import company_user
from .models import User
from .models_enterprise import RolePermission

def require_permission(permission: str):
    def checker(user: User = Depends(company_user), db: Session = Depends(get_db)):
        # Owners have full company permissions; super-admin is deliberately excluded from tenant routes.
        if user.role == "owner": return user
        row = db.query(RolePermission).filter_by(company_id=user.company_id, role=user.role, permission=permission).first()
        if not row or not row.allowed:
            raise HTTPException(status_code=403, detail=f"Missing permission: {permission}")
        return user
    return checker
