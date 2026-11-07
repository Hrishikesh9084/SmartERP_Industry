from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth_routes import router as auth_router
from .public_auth_routes import router as public_auth_router
from .phone_login_routes import router as phone_login_router

app = FastAPI(
    title="SmartERP API",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://10.121.72.34:5173",
    ],
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