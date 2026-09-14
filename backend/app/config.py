"""Application configuration."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from .env."""

    database_url: str = "postgresql+asyncpg://lotiado:lotiado@localhost:5432/lotiado"
    environment: str = "development"
    debug: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"
