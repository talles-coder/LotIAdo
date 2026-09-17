"""Tests proving RLS policies isolate tenants at the Postgres layer (FASE2-IMPL-01/FASE2-IMPL-02).

Roda contra o papel `lotiado_app` de propósito (não o dono das tabelas usado
pelo resto da suíte via `TEST_DATABASE_URL`): um superusuário/dono sempre
ignora Row-Level Security, então testar com esse papel provaria isolamento
que não existe de verdade em runtime (a app roda como `lotiado_app`, ver
infra/postgres/init/03-create-app-role.sql). Requer `make reset-db` pelo
menos uma vez após esta mudança, para os init scripts criarem o papel.

Estes testes consultam as tabelas com SQL cru, sem `WHERE tenant_id = ...`
— diferente dos testes de `test_tenant_isolation.py`, que sobem pela API e
por isso continuariam passando mesmo que a policy do banco fosse removida
(o filtro de tenant_id já existe na camada de aplicação). É só aqui, na
ausência de qualquer filtro manual, que fica provado que quem garante o
isolamento é a policy do Postgres: `DROP POLICY tenant_isolation ON
<tabela>` faz qualquer um destes testes falhar imediatamente.
"""
import os
import uuid
from typing import Awaitable, Callable

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

APP_ROLE_DATABASE_URL = os.getenv(
    "TEST_APP_DATABASE_URL",
    "postgresql+asyncpg://lotiado_app:lotiado_app@localhost:5432/lotiado_test",
)


async def _criar_tenant(admin_engine: AsyncEngine, tenant_id: uuid.UUID) -> None:
    async with admin_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenants (id, name, slug) VALUES (:id, :nome, :slug) "
                "ON CONFLICT DO NOTHING"
            ),
            {"id": tenant_id, "nome": str(tenant_id), "slug": str(tenant_id)},
        )


async def _criar_usuario(admin_engine: AsyncEngine, tenant_id: uuid.UUID) -> uuid.UUID:
    await _criar_tenant(admin_engine, tenant_id)
    usuario_id = uuid.uuid4()
    async with admin_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO users (id, email, hashed_password, full_name) "
                "VALUES (:id, :email, 'x', 'Test User')"
            ),
            {"id": usuario_id, "email": f"{usuario_id}@test.com"},
        )
    return usuario_id


async def _linha_cliente(admin_engine: AsyncEngine, tenant_id: uuid.UUID) -> None:
    await _criar_tenant(admin_engine, tenant_id)
    async with admin_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO clientes (id, tenant_id, nome, documento, contato) "
                "VALUES (gen_random_uuid(), :tenant_id, 'Fulano', '000.000.000-00', 'fulano@test.com')"
            ),
            {"tenant_id": str(tenant_id)},
        )


async def _linha_corretor(admin_engine: AsyncEngine, tenant_id: uuid.UUID) -> None:
    await _criar_tenant(admin_engine, tenant_id)
    async with admin_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO corretores (id, tenant_id, nome, contato) "
                "VALUES (gen_random_uuid(), :tenant_id, 'Fulano', 'fulano@test.com')"
            ),
            {"tenant_id": str(tenant_id)},
        )


async def _linha_loteamento(admin_engine: AsyncEngine, tenant_id: uuid.UUID) -> None:
    await _criar_tenant(admin_engine, tenant_id)
    async with admin_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO loteamentos (id, tenant_id, nome) "
                "VALUES (gen_random_uuid(), :tenant_id, 'Loteamento Teste')"
            ),
            {"tenant_id": str(tenant_id)},
        )


async def _linha_lote(admin_engine: AsyncEngine, tenant_id: uuid.UUID) -> None:
    await _criar_tenant(admin_engine, tenant_id)
    loteamento_id = uuid.uuid4()
    async with admin_engine.begin() as conn:
        await conn.execute(
            text("INSERT INTO loteamentos (id, tenant_id, nome) VALUES (:id, :tenant_id, 'Loteamento Teste')"),
            {"id": loteamento_id, "tenant_id": str(tenant_id)},
        )
        await conn.execute(
            text(
                "INSERT INTO lotes (id, tenant_id, loteamento_id, identificacao, status) "
                "VALUES (gen_random_uuid(), :tenant_id, :loteamento_id, 'Lote 1', 'disponivel')"
            ),
            {"tenant_id": str(tenant_id), "loteamento_id": loteamento_id},
        )


async def _linha_reserva_venda(admin_engine: AsyncEngine, tenant_id: uuid.UUID) -> None:
    await _criar_tenant(admin_engine, tenant_id)
    loteamento_id, lote_id, cliente_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    async with admin_engine.begin() as conn:
        await conn.execute(
            text("INSERT INTO loteamentos (id, tenant_id, nome) VALUES (:id, :tenant_id, 'Loteamento Teste')"),
            {"id": loteamento_id, "tenant_id": str(tenant_id)},
        )
        await conn.execute(
            text(
                "INSERT INTO lotes (id, tenant_id, loteamento_id, identificacao, status) "
                "VALUES (:id, :tenant_id, :loteamento_id, 'Lote 1', 'disponivel')"
            ),
            {"id": lote_id, "tenant_id": str(tenant_id), "loteamento_id": loteamento_id},
        )
        await conn.execute(
            text(
                "INSERT INTO clientes (id, tenant_id, nome, documento, contato) "
                "VALUES (:id, :tenant_id, 'Fulano', '000.000.000-00', 'fulano@test.com')"
            ),
            {"id": cliente_id, "tenant_id": str(tenant_id)},
        )
        await conn.execute(
            text(
                "INSERT INTO reservas_vendas (id, tenant_id, lote_id, cliente_id, tipo, status) "
                "VALUES (gen_random_uuid(), :tenant_id, :lote_id, :cliente_id, 'reserva', 'reservado')"
            ),
            {"tenant_id": str(tenant_id), "lote_id": lote_id, "cliente_id": cliente_id},
        )


async def _linha_audit_log(admin_engine: AsyncEngine, tenant_id: uuid.UUID) -> None:
    usuario_id = await _criar_usuario(admin_engine, tenant_id)
    async with admin_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO audit_log (id, tenant_id, usuario_id, acao, entidade, entidade_id) "
                "VALUES (gen_random_uuid(), :tenant_id, :usuario_id, 'criacao', 'teste', gen_random_uuid())"
            ),
            {"tenant_id": str(tenant_id), "usuario_id": usuario_id},
        )


CriarLinha = Callable[[AsyncEngine, uuid.UUID], Awaitable[None]]

TABELAS_COM_RLS: list[tuple[str, CriarLinha]] = [
    ("clientes", _linha_cliente),
    ("corretores", _linha_corretor),
    ("loteamentos", _linha_loteamento),
    ("lotes", _linha_lote),
    ("reservas_vendas", _linha_reserva_venda),
    ("audit_log", _linha_audit_log),
]


async def _ativar_rls(admin_engine: AsyncEngine, tabela: str) -> None:
    """Espelha a policy criada pelas migrations (20260915160000 / 20260916090000).

    O schema de teste vem de `Base.metadata.create_all` (fixture `async_engine`
    em conftest.py), não de `alembic upgrade head`, então a policy não existe
    no banco de teste a menos que seja recriada aqui.
    """
    async with admin_engine.begin() as conn:
        await conn.execute(text(f"ALTER TABLE {tabela} ENABLE ROW LEVEL SECURITY"))
        await conn.execute(text(f"ALTER TABLE {tabela} FORCE ROW LEVEL SECURITY"))
        await conn.execute(
            text(
                f"CREATE POLICY tenant_isolation ON {tabela} "
                "USING (tenant_id = current_setting('app.tenant_id', true)::uuid) "
                "WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)"
            )
        )


@pytest_asyncio.fixture
async def app_role_engine(async_engine: AsyncEngine):
    """Expõe uma engine conectada como o papel restrito `lotiado_app`.

    A policy em si é ativada dentro de cada teste (via `_ativar_rls`), já
    que a tabela alvo varia por caso parametrizado.
    """
    engine = create_async_engine(APP_ROLE_DATABASE_URL, future=True)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.mark.asyncio
@pytest.mark.parametrize("tabela,criar_linha", TABELAS_COM_RLS, ids=[t for t, _ in TABELAS_COM_RLS])
async def test_query_sem_tenant_id_setado_retorna_zero_linhas(
    async_engine: AsyncEngine, app_role_engine: AsyncEngine, tabela: str, criar_linha: CriarLinha
):
    """Sem `app.tenant_id` na sessão, a policy falha fechada (não aberta), em toda tabela protegida."""
    await _ativar_rls(async_engine, tabela)
    await criar_linha(async_engine, uuid.uuid4())

    async with app_role_engine.connect() as conn:
        result = await conn.execute(text(f"SELECT * FROM {tabela}"))
        assert result.fetchall() == []


@pytest.mark.asyncio
@pytest.mark.parametrize("tabela,criar_linha", TABELAS_COM_RLS, ids=[t for t, _ in TABELAS_COM_RLS])
async def test_tenant_so_enxerga_suas_proprias_linhas(
    async_engine: AsyncEngine, app_role_engine: AsyncEngine, tabela: str, criar_linha: CriarLinha
):
    """Um tenant autenticado não vê linhas de outro tenant, mesmo sem WHERE, em toda tabela protegida."""
    await _ativar_rls(async_engine, tabela)
    tenant_a, tenant_b = uuid.uuid4(), uuid.uuid4()
    await criar_linha(async_engine, tenant_a)
    await criar_linha(async_engine, tenant_b)

    async with app_role_engine.connect() as conn:
        await conn.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(tenant_a)},
        )
        result = await conn.execute(text(f"SELECT tenant_id FROM {tabela}"))
        linhas = result.fetchall()

    assert len(linhas) == 1
    assert str(linhas[0].tenant_id) == str(tenant_a)


@pytest.mark.asyncio
async def test_insert_com_tenant_id_de_outro_tenant_e_bloqueado(
    async_engine: AsyncEngine, app_role_engine: AsyncEngine
):
    """WITH CHECK impede gravar uma linha marcada com o tenant_id de outro tenant.

    A expressão do WITH CHECK é idêntica em todas as tabelas (mesma policy
    `tenant_isolation`), então um único exemplo representativo já comprova o
    mecanismo — repetir por tabela só duplicaria setup de FKs sem cobrir
    nada novo.
    """
    await _ativar_rls(async_engine, "clientes")
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
