"""Database configuration and session management."""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, MetaData

from app.config import Settings

settings = Settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
)

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

metadata = MetaData()


async def get_db() -> AsyncSession:
    """Dependency to get database session."""
    async with async_session() as session:
        yield session
