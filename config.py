# hms_web/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ── Flask ──────────────────────────────────────────
    SECRET_KEY = os.getenv("SECRET_KEY", "hms-super-secret-key-change-in-production")
    DEBUG      = os.getenv("DEBUG", "True") == "True"

    # ── MySQL ──────────────────────────────────────────
    DB_HOST     = os.getenv("DB_HOST",     "localhost")
    DB_PORT     = int(os.getenv("DB_PORT", "3306"))
    DB_NAME     = os.getenv("DB_NAME",     "hospital_db")
    DB_USER     = os.getenv("DB_USER",     "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "Enter YouR Password Here")  # ← change this

    # ── Session ────────────────────────────────────────
    SESSION_TYPE       = "filesystem"
    SESSION_PERMANENT  = False
    PERMANENT_SESSION_LIFETIME = 3600   # 1 hour
