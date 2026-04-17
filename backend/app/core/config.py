from pydantic_settings import BaseSettings
import os
from typing import Optional

class Settings(BaseSettings):
    # Application Settings
    PROJECT_NAME: str = "SolShare Energy Sharing and Trading System"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./solshare.db")
    SECRET_KEY: str 
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    RESET_TOKEN_EXPIRE_MINUTES: int = 30

    # Admin User Settings
    ADMIN_EMAIL: str
    ADMIN_PASSWORD: str 
    ADMIN_FULL_NAME: str = ("System Administrator")

    # Email Settings
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None

    # Frontend URL
    FRONTEND_URL: str = "http://localhost:5173"

    model_config = {
        "case_sensitive": True,
        "env_file": ".env"
    }
settings = Settings()
