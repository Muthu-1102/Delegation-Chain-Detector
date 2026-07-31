"""
Application configuration.

Loaded from environment variables / .env file. See backend/.env.example.
"""

from functools import lru_cache

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_DEFAULTS = {"change-me-in-production", "", "secret", "changeme"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Delegation Chain Governor"
    ENVIRONMENT: str = "development"  # "development" | "staging" | "production"

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

    # CORS -- comma-separated list, e.g. "https://app.example.com,https://admin.example.com"
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.FRONTEND_ORIGIN.split(",") if origin.strip()]

    @model_validator(mode="after")
    def _enforce_production_secrets(self) -> "Settings":
        if self.ENVIRONMENT == "production":
            if self.JWT_SECRET_KEY.strip().lower() in _INSECURE_DEFAULTS:
                raise RuntimeError(
                    "JWT_SECRET_KEY is unset or using an insecure default while "
                    "ENVIRONMENT=production. Generate one with: "
                    "python -c \"import secrets; print(secrets.token_urlsafe(64))\" "
                    "and set it via your secret manager / env, never in source."
                )
            if len(self.JWT_SECRET_KEY) < 32:
                raise RuntimeError(
                    "JWT_SECRET_KEY is too short for production use (<32 chars)."
                )
            if "dcg_password" in self.DATABASE_URL or "change-me" in self.DATABASE_URL:
                raise RuntimeError(
                    "DATABASE_URL still contains a default/placeholder credential "
                    "while ENVIRONMENT=production."
                )
            if self.FRONTEND_ORIGIN in ("", "*", "http://localhost:5173"):
                raise RuntimeError(
                    "FRONTEND_ORIGIN must be set to your real frontend origin(s) "
                    "in production -- wildcard/localhost CORS is not allowed."
                )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()