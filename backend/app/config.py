import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

APP_ENV = os.getenv("APP_ENV", "development")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./smarterp.db")
SECRET_KEY = os.getenv("SECRET_KEY", "DEV_ONLY_CHANGE_ME")
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "60"))
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
SUPERADMIN_EMAIL = os.getenv("SUPERADMIN_EMAIL", "admin@smarterp.local").lower()
SUPERADMIN_PASSWORD = os.getenv("SUPERADMIN_PASSWORD", "ChangeThisAdminPassword123!")
OTP_EXPIRY_MINUTES = int(os.getenv("OTP_EXPIRY_MINUTES", "10"))
DEV_SHOW_OTP = os.getenv("DEV_SHOW_OTP", "false").lower() == "true"
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv(
    "GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback"
)

RAZORPAY_KEY_ID=os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET=os.getenv("RAZORPAY_KEY_SECRET", "")
RAZORPAY_WEBHOOK_SECRET=os.getenv("RAZORPAY_WEBHOOK_SECRET", "")
STRIPE_SECRET_KEY=os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET=os.getenv("STRIPE_WEBHOOK_SECRET", "")
