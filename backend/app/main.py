from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .public_auth_routes import router as public_auth_router
from .phone_login_routes import router as phone_login_router
from .admin_routes import router as admin_router
from .ai_routes import router as ai_router
from .billing_routes import router as billing_router
from .business_routes import router as business_router
from .config import FRONTEND_ORIGIN
from .enterprise_routes import router as enterprise_router
from .organization_routes import router as organization_router

app = FastAPI(
    title="SmartERP API",
    version="1.0.0"
)

allowed_origins = {
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "capacitor://localhost",
    "http://localhost",
}
allowed_origins.update(
    origin.strip()
    for origin in FRONTEND_ORIGIN.split(",")
    if origin.strip()
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(allowed_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(public_auth_router)
app.include_router(phone_login_router)
app.include_router(admin_router)
app.include_router(ai_router)
app.include_router(billing_router)
app.include_router(business_router)
app.include_router(enterprise_router)
app.include_router(organization_router)


@app.get("/")
def root():
    return {
        "message": "SmartERP API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }