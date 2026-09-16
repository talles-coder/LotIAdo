"""Tests proving RLS policies isolate tenants at the Postgres layer (FASE2-IMPL-01).

Roda contra o papel `lotiado_app` de propósito (não o dono das tabelas usado
pelo resto da suíte via `TEST_DATABASE_URL`): um superusuário/dono sempre
ignora Row-Level Security, então testar com esse papel provaria isolamento
que não existe de verdade em runtime (a app roda como `lotiado_app`, ver
infra/postgres/init/03-create-app-role.sql). Requer `make reset-db` pelo
menos uma vez após esta mudança, para os init scripts criarem o papel.
"""
import os
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

APP_ROLE_DATABASE_URL = os.getenv(
    "TEST_APP_DATABASE_URL",
    "postgresql+asyncpg://lotiado_app:lotiado_app@localhost:5432/lotiado_test",
)


async def _enable_rls_on_clientes(admin_engine: AsyncEngine) -> None:
    async with admin_engine.begin() as conn:
        await conn.execute(text("ALTER TABLE clientes ENABLE ROW LEVEL SECURITY"))
        await conn.execute(text("ALTER TABLE clientes FORCE ROW LEVEL SECURITY"))
        await conn.execute(
            text(
                "CREATE POLICY tenant_isolation ON clientes "
                "USING (tenant_id = current_setting('app.tenant_id', true)::uuid) "
                "WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)"
            )
        )


async def _criar_cliente(admin_engine: AsyncEngine, tenant_id: uuid.UUID) -> None:
    async with admin_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenants (id, name, slug) VALUES (:id, :nome, :slug) "
                "ON CONFLICT DO NOTHING"
            ),
            {"id": tenant_id, "nome": str(tenant_id), "slug": str(tenant_id)},
        )
        await conn.execute(
            text(
                "INSERT INTO clientes (id, tenant_id, nome, documento, contato) "
                "VALUES (gen_random_uuid(), :tenant_id, 'Fulano', '000.000.000-00', 'fulano@test.com')"
            ),
            {"tenant_id": str(tenant_id)},
        )


@pytest_asyncio.fixture
async def app_role_engine(async_engine: AsyncEngine):
    """Ativa RLS em `clientes` (como dona) e expõe uma conexão do papel restrito."""
    await _enable_rls_on_clientes(async_engine)

    engine = create_async_engine(APP_ROLE_DATABASE_URL, future=True)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_query_sem_tenant_id_setado_retorna_zero_linhas(
    async_engine: AsyncEngine, app_role_engine: AsyncEngine
):
    """Sem `app.tenant_id` na sessão, a policy falha fechada (não aberta)."""
    await _criar_cliente(async_engine, uuid.uuid4())

    async with app_role_engine.connect() as conn:
        result = await conn.execute(text("SELECT * FROM clientes"))
        assert result.fetchall() == []


@pytest.mark.asyncio
async def test_tenant_so_enxerga_seus_proprios_clientes(
    async_engine: AsyncEngine, app_role_engine: AsyncEngine
):
    """Um tenant autenticado não vê clientes de outro tenant, mesmo sem WHERE."""
    tenant_a, tenant_b = uuid.uuid4(), uuid.uuid4()
    await _criar_cliente(async_engine, tenant_a)
    await _criar_cliente(async_engine, tenant_b)

    async with app_role_engine.connect() as conn:
        await conn.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(tenant_a)},
        )
        result = await conn.execute(text("SELECT tenant_id FROM clientes"))
        linhas = result.fetchall()

    assert len(linhas) == 1
    assert str(linhas[0].tenant_id) == str(tenant_a)


@pytest.mark.asyncio
async def test_insert_com_tenant_id_de_outro_tenant_e_bloqueado(
    async_engine: AsyncEngine, app_role_engine: AsyncEngine
):
    """WITH CHECK impede gravar uma linha marcada com o tenant_id de outro tenant."""
    tenant_a, tenant_b = uuid.uuid4(), uuid.uuid4()
    async with async_engine.begin() as conn:
        for tenant_id in (tenant_a, tenant_b):
            await conn.execute(
                text("INSERT INTO tenants (id, name, slug) VALUES (:id, :nome, :slug)"),
                {"id": tenant_id, "nome": str(tenant_id), "slug": str(tenant_id)},
            )

    async with app_role_engine.connect() as conn:
        await conn.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(tenant_a)},
        )
        with pytest.raises(Exception):
            await conn.execute(
                text(
                    "INSERT INTO clientes (id, tenant_id, nome, documento, contato) "
                    "VALUES (gen_random_uuid(), :tenant_id, 'Fulano', '000.000.000-00', 'fulano@test.com')"
                ),
                {"tenant_id": str(tenant_b)},
            )
