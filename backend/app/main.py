from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth_routes import router as auth_router
from .public_auth_routes import router as public_auth_router
from .phone_login_routes import router as phone_login_router
from .config import FRONTEND_ORIGIN

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
app.include_router(auth_router)
app.include_router(public_auth_router)
app.include_router(phone_login_router)


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