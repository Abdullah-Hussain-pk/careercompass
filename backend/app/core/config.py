"""
CareerCompass – Application Configuration
Uses pydantic-settings to load from environment / .env file.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ── Application ───────────────────────────────────────────────
    APP_NAME: str = "CareerCompass"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"

    # ── Database ──────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./careercompass.db"
    DATABASE_URL_SYNC: str = "sqlite:///./careercompass.db"

    # ── Security ──────────────────────────────────────────────────
    SECRET_KEY: str = "insecure_dev_key_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # NFR-2: 30-minute tokens

    # ── CORS ──────────────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    # ── Rate limiting ─────────────────────────────────────────────
    LOGIN_RATE_LIMIT: str = "10/minute"
    REGISTER_RATE_LIMIT: str = "5/minute"

    # ── Recommendation defaults ────────────────────────────────────
    DEFAULT_W1: float = 0.5   # interest weight
    DEFAULT_W2: float = 0.3   # skill weight
    DEFAULT_W3: float = 0.2   # degree weight

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
