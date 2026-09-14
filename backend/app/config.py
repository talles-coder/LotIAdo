"""Application configuration."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from .env."""

    database_url: str = "postgresql+asyncpg://lotiado:lotiado@localhost:5432/lotiado"
    environment: str = "development"
    debug: bool = True

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"
