from datetime import datetime, timedelta
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session
from .models_enterprise import RateLimitEvent

def enforce_rate_limit(db: Session, key: str, limit: int = 5, window_seconds: int = 900):
    now=datetime.utcnow(); cutoff=now-timedelta(seconds=window_seconds)
    db.query(RateLimitEvent).filter(RateLimitEvent.created_at < cutoff).delete(synchronize_session=False)
    count=db.query(RateLimitEvent).filter(RateLimitEvent.bucket==key, RateLimitEvent.created_at>=cutoff).count()
    if count >= limit:
        raise HTTPException(status_code=429, detail="Too many attempts. Please wait before trying again.")
    db.add(RateLimitEvent(bucket=key)); db.commit()

def client_key(request: Request, purpose: str, identity: str):
    ip=request.client.host if request.client else 'unknown'
    return f"{purpose}:{ip}:{identity.lower()[:120]}"
