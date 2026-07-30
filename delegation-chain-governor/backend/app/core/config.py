"""
Application configuration.

Loaded from environment variables / .env file. See backend/.env.example.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Delegation Chain Governor"
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = (
        "postgresql+asyncpg://dcg_user:dcg_password@postgres:5432/dcg_db"
    )

    # JWT / Delegation Chain Governor
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_TTL_SECONDS: int = 900
    JWT_DELEGATION_TOKEN_TTL_SECONDS: int = 120

    # Groq API
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # CORS
    FRONTEND_ORIGIN: str = "http://localhost:5173"


@lru_cache
def get_settings() -> Settings:
    return Settings()
