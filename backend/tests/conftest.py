"""Pytest configuration and fixtures."""
import asyncio
import os
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from app.common.models import Base
from app.database import get_db
from app.identity.domain.models import Permission, RolePermission
from app.main import app

load_dotenv()

# Mantém as fixtures de teste equivalentes ao seed de produção (ver migration
# 20260915170000): admin/gestor/corretor recebem todas as permissões, então
# os testes existentes (que usam role="admin") continuam passando sem
# precisar conhecer as permissões de cada rota.
PERMISSOES_SEED = (
    "clientes:gerenciar",
    "corretores:gerenciar",
    "loteamentos_lotes:gerenciar",
)
PAPEIS_SEED = ("admin", "gestor", "corretor")


async def _seed_permissions(engine) -> None:
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        permissoes = [Permission(key=key, description=key) for key in PERMISSOES_SEED]
        session.add_all(permissoes)
        await session.flush()

        session.add_all(
            RolePermission(role=papel, permission_id=permissao.id)
            for papel in PAPEIS_SEED
            for permissao in permissoes
        )
        await session.commit()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def async_engine():
    """Create a test database engine."""
    test_db_url = os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://lotiado:lotiado@localhost:5432/lotiado_test")
    engine = create_async_engine(
        test_db_url,
        echo=False,
        future=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await _seed_permissions(engine)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """HTTP client for the FastAPI app, backed by the test database session."""

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
