from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "SolShare Energy Sharing System"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./solshare.db")
    SECRET_KEY: str = "YOUR_SUPER_SECRET_KEY_CHANGE_THIS_IN_PROD"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@solshare.com")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")
    ADMIN_FULL_NAME: str = os.getenv("ADMIN_FULL_NAME", "System Administrator")

    class Config:
        case_sensitive = True

settings = Settings()
