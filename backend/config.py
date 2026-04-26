# ============================================================
# CareerLens – Backend Configuration
# File: backend/config.py
# Loads all settings from environment variables / .env file
# ============================================================

from typing import List
from functools import lru_cache
from pathlib import Path

try:
    # Preferred for pydantic v2
    from pydantic_settings import BaseSettings  # type: ignore
    _USING_PYDANTIC_SETTINGS = True
except Exception:
    # Backward-compatible fallback when pydantic-settings is not installed
    from pydantic.v1 import BaseSettings  # type: ignore
    _USING_PYDANTIC_SETTINGS = False


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    All values can be overridden via a .env file in backend/.
    """

    # ----------------------------------------------------------
    # App
    # ----------------------------------------------------------
    ENVIRONMENT: str = "development"           # development | production
    SECRET_KEY: str = "change-me-in-production"
    TRUSTED_HOSTS: List[str] = ["localhost", "127.0.0.1"]

    # ----------------------------------------------------------
    # CORS
    # ----------------------------------------------------------
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # ----------------------------------------------------------
    # Supabase
    # ----------------------------------------------------------
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""                     # Service role key (backend only)
    SUPABASE_ANON_KEY: str = ""                # Anon key (if needed)

    # ----------------------------------------------------------
    # AI Providers
    # ----------------------------------------------------------
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"    # fallback chain is handled in gemini_service.py
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # ----------------------------------------------------------
    # GitHub API
    # ----------------------------------------------------------
    GITHUB_TOKEN: str = ""                     # Optional – raises rate limit

    # ----------------------------------------------------------
    # News APIs
    # ----------------------------------------------------------
    NEWSAPI_KEY: str = ""                      # https://newsapi.org (free tier)
    # RSS feeds are used as fallback (no key needed)

    # ----------------------------------------------------------
    # Payment (Stripe / Razorpay – placeholder)
    # ----------------------------------------------------------
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""

    # ----------------------------------------------------------
    # Freemium limits
    # ----------------------------------------------------------
    FREEMIUM_MAX_ANALYSES: int = 1
    FREEMIUM_MAX_INTERVIEWS: int = 1
    FREEMIUM_MAX_CHATBOT_MSGS: int = 20
    FREEMIUM_MAX_PORTFOLIO_GENS: int = 4

    # ----------------------------------------------------------
    # File Upload
    # ----------------------------------------------------------
    MAX_RESUME_SIZE_MB: int = 5
    ALLOWED_RESUME_TYPES: List[str] = ["application/pdf"]

    if _USING_PYDANTIC_SETTINGS:
        model_config = {
            "env_file": str(Path(__file__).resolve().parent / ".env"),
            "env_file_encoding": "utf-8",
            "case_sensitive": True,
        }
    else:
        class Config:
            env_file = str(Path(__file__).resolve().parent / ".env")
            env_file_encoding = "utf-8"
            case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance – call get_settings() anywhere."""
    return Settings()


# Singleton used throughout the app
settings = get_settings()
