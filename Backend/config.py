"""
Configuration Management for Chat-to-CAD Platform
Loads environment variables and provides typed settings
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional
from pathlib import Path

# ── Native model — not overridable ──
# This app is locked to Claude Opus 4.7 by design. The model id is a module
# constant; any AI_MODEL_NAME value supplied via .env or environment is
# ignored on purpose so the UX, prompt cache hits, and pricing stay stable.
NATIVE_MODEL_ID: str = "claude-opus-4-7"


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Keys
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # AI Configuration — the model id is fixed; env overrides are ignored.
    AI_MODEL_NAME: str = NATIVE_MODEL_ID
    AI_MAX_TOKENS: int = 8192
    AI_TEMPERATURE: float = 0.3

    @field_validator("AI_MODEL_NAME", mode="before")
    @classmethod
    def _force_native_model(cls, _value):
        # Always return the native model id regardless of what the env says.
        return NATIVE_MODEL_ID
    
    # Server Configuration
    PORT: int = 3001
    HOST: str = "0.0.0.0"
    
    # Paths
    EXPORTS_DIR: Path = Path(__file__).parent.parent / "exports"
    CAD_DIR: Path = EXPORTS_DIR / "cad"
    
    # Supabase Database Configuration
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    # Service role key bypasses RLS — required for backend project/build persistence
    # because RLS policies gate rows by auth.uid() which is NULL for anon-key requests.
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None

    # Authentication
    REQUIRE_AUTH: bool = False  # Set True in .env to enforce JWT auth on write endpoints
    SUPABASE_JWT_SECRET: Optional[str] = None  # Supabase JWT secret for signature verification

    # CORS — comma-separated allowed origins (set in .env for production)
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"

    # Rate limiting
    RATE_LIMIT_BUILD: str = "5/minute"   # max AI build requests per IP
    RATE_LIMIT_DEFAULT: str = "60/minute"

    # Stripe Billing
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    STRIPE_PRO_PRICE_MONTHLY: Optional[str] = None   # price_xxx from Stripe dashboard
    STRIPE_PRO_PRICE_YEARLY: Optional[str] = None
    STRIPE_ENT_PRICE_MONTHLY: Optional[str] = None
    STRIPE_ENT_PRICE_YEARLY: Optional[str] = None
    FRONTEND_URL: str = "http://localhost:3000"

    class Config:
        env_file = Path(__file__).parent.parent / ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env

# Singleton settings instance
settings = Settings()

# Ensure directories exist
settings.CAD_DIR.mkdir(parents=True, exist_ok=True)
