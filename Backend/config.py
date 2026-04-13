"""
Configuration Management for Chat-to-CAD Platform
Loads environment variables and provides typed settings
"""

from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Keys
    ANTHROPIC_API_KEY: str
    OPENAI_API_KEY: Optional[str] = None
    
    # AI Configuration
    AI_MODEL_NAME: str = "claude-opus-4-6"
    AI_MAX_TOKENS: int = 8192
    AI_TEMPERATURE: float = 0.3
    
    # Server Configuration
    PORT: int = 3001
    HOST: str = "0.0.0.0"
    
    # Paths
    EXPORTS_DIR: Path = Path(__file__).parent.parent / "exports"
    CAD_DIR: Path = EXPORTS_DIR / "cad"
    
    # Supabase Database Configuration
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None

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
