import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Bangladesh Legal Intelligence SaaS"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "bangladesh-legal-ai-saas-super-secret-key-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database
    # Default to SQLite for fast local development and testing, supports PostgreSQL
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./legal_saas.db")

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]

    # AI Configuration (Model Agnostic)
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "gemini")  # gemini, openai, mock
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Uploads & Exports
    STORAGE_DIR: str = os.getenv("STORAGE_DIR", "./storage")

    model_config = {"case_sensitive": True, "env_file": ".env", "extra": "ignore"}

settings = Settings()
