"""Testes de isolamento de tenant ponta a ponta (SCRUM-58 / FASE2-IMPL-02).

Cobre, para cada endpoint de leitura/escrita de `loteamentos_lotes`,
`clientes`, `corretores` e `vendas_reservas`: uma sessão autenticada no
Tenant A nunca vê nem edita dados do Tenant B — inclusive forjando, na URL
ou no corpo da requisição, ids que pertencem a outro tenant.

Diferente da fixture `client` de conftest.py (que usa o papel dono das
tabelas, sem RLS, e só exercita o filtro de tenant da camada de aplicação),
aqui a stack sobe com Row-Level Security realmente ativo no schema de teste
e com o papel restrito `lotiado_app` (o mesmo que a aplicação usa em
runtime — ver infra/postgres/init/03-create-app-role.sql), provando
isolamento de ponta a ponta. A prova de que a *policy* do Postgres é
necessária (e não só o filtro de aplicação) fica em `test_rls.py`, que
consulta as tabelas sem nenhum WHERE de tenant.
"""
from dataclasses import dataclass
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import Settings
from app.database import get_db
from app.identity.application.security import create_access_token, hash_password
from app.identity.domain.models import User, UserTenantMembership
from app.main import app
from app.tenancy.domain.models import Tenant
from tests.test_rls import APP_ROLE_DATABASE_URL, TABELAS_COM_RLS, _ativar_rls


@pytest_asyncio.fixture
async def rls_engine(async_engine: AsyncEngine) -> AsyncGenerator[AsyncEngine, None]:
    """Ativa RLS (como dona) nas tabelas de domínio e expõe uma engine do papel `lotiado_app`."""
    for tabela, _criar_linha in TABELAS_COM_RLS:
        await _ativar_rls(async_engine, tabela)

    engine = create_async_engine(APP_ROLE_DATABASE_URL, future=True)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def rls_session(rls_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    session_maker = sessionmaker(rls_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def rls_client(rls_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Client HTTP com `get_db` servido pelo papel restrito, com RLS ativo no schema."""

    async def _override_get_db():
        yield rls_session

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


async def _criar_usuario_com_tenant(db: AsyncSession, tenant_slug: str) -> str:
    """Cria um usuário com membership em um tenant e retorna o token JWT.

    `tenants`/`users`/`user_tenant_membership` ficam fora do RLS de propósito
    (ver TENANT_CONVENTION.md), então criá-los pelo papel `lotiado_app` (via
    `rls_session`) funciona normalmente.
    """
    tenant = Tenant(name=tenant_slug, slug=tenant_slug)
    db.add(tenant)
    await db.flush()

    user = User(
        email=f"{tenant_slug}@test.com",
        hashed_password=hash_password("senha123"),
        full_name="Test User",
    )
    db.add(user)
    await db.flush()

    db.add(UserTenantMembership(user_id=user.id, tenant_id=tenant.id, role="admin"))
    await db.commit()

    return create_access_token(user.id, tenant.id, Settings())


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _criar_loteamento(client: AsyncClient, token: str, nome: str = "Loteamento Teste") -> str:
    response = await client.post("/loteamentos", json={"nome": nome}, headers=_auth_headers(token))
    assert response.status_code == 201
    return response.json()["id"]


async def _criar_lote(client: AsyncClient, token: str, loteamento_id: str, identificacao: str = "Lote 1") -> str:
    response = await client.post(
        f"/loteamentos/{loteamento_id}/lotes",
        json={"identificacao": identificacao},
        headers=_auth_headers(token),
    )
    assert response.status_code == 201
    return response.json()["id"]


async def _criar_cliente(client: AsyncClient, token: str, nome: str = "Cliente Teste") -> str:
    response = await client.post(
        "/clientes",
        json={"nome": nome, "documento": "12345678900", "contato": "cliente@test.com"},
        headers=_auth_headers(token),
    )
    assert response.status_code == 201
    return response.json()["id"]


async def _criar_corretor(client: AsyncClient, token: str, nome: str = "Corretor Teste") -> str:
    response = await client.post(
        "/corretores",
        json={"nome": nome, "contato": "corretor@test.com"},
        headers=_auth_headers(token),
    )
    assert response.status_code == 201
    return response.json()["id"]


async def _criar_reserva(client: AsyncClient, token: str, lote_id: str, cliente_id: str) -> dict:
    response = await client.post(
        "/reservas",
        json={"lote_id": lote_id, "cliente_id": cliente_id},
        headers=_auth_headers(token),
    )
    assert response.status_code == 201
    return response.json()


@dataclass
class _DoisTenants:
    """Dois tenants isolados: Tenant A com um conjunto completo de dados de domínio."""

    token_a: str
    token_b: str
    loteamento_a: str
    lote_a: str
    cliente_a: str
    corretor_a: str
    reserva_a: dict


@pytest_asyncio.fixture
async def dois_tenants(rls_client: AsyncClient, rls_session: AsyncSession) -> _DoisTenants:
    """Tenant A com um loteamento+lote, cliente, corretor e uma reserva; Tenant B só autenticado."""
    token_a = await _criar_usuario_com_tenant(rls_session, "iso-tenant-a")
    token_b = await _criar_usuario_com_tenant(rls_session, "iso-tenant-b")

    loteamento_a = await _criar_loteamento(rls_client, token_a)
    lote_a = await _criar_lote(rls_client, token_a, loteamento_a)
    cliente_a = await _criar_cliente(rls_client, token_a)
    corretor_a = await _criar_corretor(rls_client, token_a)
    reserva_a = await _criar_reserva(rls_client, token_a, lote_a, cliente_a)

    return _DoisTenants(
        token_a=token_a,
        token_b=token_b,
        loteamento_a=loteamento_a,
        lote_a=lote_a,
        cliente_a=cliente_a,
        corretor_a=corretor_a,
        reserva_a=reserva_a,
    )


# --- loteamentos ---------------------------------------------------------


@pytest.mark.asyncio
async def test_listar_loteamentos_isola_por_tenant_com_rls_ativo(
    rls_client: AsyncClient, dois_tenants: _DoisTenants
):
    response = await rls_client.get("/loteamentos", headers=_auth_headers(dois_tenants.token_b))
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_obter_loteamento_de_outro_tenant_retorna_404(rls_client: AsyncClient, dois_tenants: _DoisTenants):
    response = await rls_client.get(
        f"/loteamentos/{dois_tenants.loteamento_a}", headers=_auth_headers(dois_tenants.token_b)
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_atualizar_loteamento_de_outro_tenant_retorna_404(rls_client: AsyncClient, dois_tenants: _DoisTenants):
    response = await rls_client.patch(
        f"/loteamentos/{dois_tenants.loteamento_a}",
        json={"nome": "Nome Forjado"},
        headers=_auth_headers(dois_tenants.token_b),
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_remover_loteamento_de_outro_tenant_retorna_404(rls_client: AsyncClient, dois_tenants: _DoisTenants):
    response = await rls_client.delete(
        f"/loteamentos/{dois_tenants.loteamento_a}", headers=_auth_headers(dois_tenants.token_b)
    )
    assert response.status_code == 404


# --- lotes -----------------------------------------------------------------


@pytest.mark.asyncio
async def test_criar_lote_em_loteamento_de_outro_tenant_retorna_404(
    rls_client: AsyncClient, dois_tenants: _DoisTenants
):
    response = await rls_client.post(
        f"/loteamentos/{dois_tenants.loteamento_a}/lotes",
        json={"identificacao": "Lote Forjado"},
        headers=_auth_headers(dois_tenants.token_b),
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_listar_lotes_de_loteamento_de_outro_tenant_retorna_vazio(
    rls_client: AsyncClient, dois_tenants: _DoisTenants
):
    response = await rls_client.get(
        f"/loteamentos/{dois_tenants.loteamento_a}/lotes", headers=_auth_headers(dois_tenants.token_b)
    )
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_obter_lote_de_outro_tenant_retorna_404(rls_client: AsyncClient, dois_tenants: _DoisTenants):
    response = await rls_client.get(f"/lotes/{dois_tenants.lote_a}", headers=_auth_headers(dois_tenants.token_b))
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_atualizar_lote_de_outro_tenant_retorna_404(rls_client: AsyncClient, dois_tenants: _DoisTenants):
    response = await rls_client.patch(
        f"/lotes/{dois_tenants.lote_a}", json={"preco": "1.00"}, headers=_auth_headers(dois_tenants.token_b)
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_transicionar_status_de_lote_de_outro_tenant_retorna_404(
    rls_client: AsyncClient, dois_tenants: _DoisTenants
):
    response = await rls_client.patch(
        f"/lotes/{dois_tenants.lote_a}/status",
        json={"status": "reservado"},
        headers=_auth_headers(dois_tenants.token_b),
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_remover_lote_de_outro_tenant_retorna_404(rls_client: AsyncClient, dois_tenants: _DoisTenants):
    response = await rls_client.delete(f"/lotes/{dois_tenants.lote_a}", headers=_auth_headers(dois_tenants.token_b))
    assert response.status_code == 404


# --- clientes ----------------------------------------------------------


@pytest.mark.asyncio
async def test_listar_clientes_isola_por_tenant_com_rls_ativo(rls_client: AsyncClient, dois_tenants: _DoisTenants):
    response = await rls_client.get("/clientes", headers=_auth_headers(dois_tenants.token_b))
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_obter_cliente_de_outro_tenant_retorna_404(rls_client: AsyncClient, dois_tenants: _DoisTenants):
    response = await rls_client.get(f"/clientes/{dois_tenants.cliente_a}", headers=_auth_headers(dois_tenants.token_b))
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_atualizar_cliente_de_outro_tenant_retorna_404(rls_client: AsyncClient, dois_tenants: _DoisTenants):
    response = await rls_client.patch(
        f"/clientes/{dois_tenants.cliente_a}",
        json={"nome": "Nome Forjado"},
        headers=_auth_headers(dois_tenants.token_b),
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_remover_cliente_de_outro_tenant_retorna_404(rls_client: AsyncClient, dois_tenants: _DoisTenants):
    response = await rls_client.delete(
        f"/clientes/{dois_tenants.cliente_a}", headers=_auth_headers(dois_tenants.token_b)
    )
    assert response.status_code == 404


# --- corretores --------------------------------------------------------


@pytest.mark.asyncio
async def test_listar_corretores_isola_por_tenant_com_rls_ativo(rls_client: AsyncClient, dois_tenants: _DoisTenants):
    response = await rls_client.get("/corretores", headers=_auth_headers(dois_tenants.token_b))
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_obter_corretor_de_outro_tenant_retorna_404(rls_client: AsyncClient, dois_tenants: _DoisTenants):
    response = await rls_client.get(
        f"/corretores/{dois_tenants.corretor_a}", headers=_auth_headers(dois_tenants.token_b)
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_atualizar_corretor_de_outro_tenant_retorna_404(rls_client: AsyncClient, dois_tenants: _DoisTenants):
    response = await rls_client.patch(
        f"/corretores/{dois_tenants.corretor_a}",
        json={"nome": "Nome Forjado"},
        headers=_auth_headers(dois_tenants.token_b),
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_remover_corretor_de_outro_tenant_retorna_404(rls_client: AsyncClient, dois_tenants: _DoisTenants):
    response = await rls_client.delete(
        f"/corretores/{dois_tenants.corretor_a}", headers=_auth_headers(dois_tenants.token_b)
    )
    assert response.status_code == 404


# --- vendas_reservas -----------------------------------------------------


@pytest.mark.asyncio
async def test_criar_reserva_com_lote_de_outro_tenant_retorna_404(
    rls_client: AsyncClient, dois_tenants: _DoisTenants
):
    """Forjar o `lote_id` de outro tenant no corpo da requisição não deve reservar nada."""
    cliente_b = await _criar_cliente(rls_client, dois_tenants.token_b)

    response = await rls_client.post(
        "/reservas",
        json={"lote_id": dois_tenants.lote_a, "cliente_id": cliente_b},
        headers=_auth_headers(dois_tenants.token_b),
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_criar_reserva_com_cliente_de_outro_tenant_retorna_404(
    rls_client: AsyncClient, dois_tenants: _DoisTenants
):
    """Forjar o `cliente_id` de outro tenant no corpo da requisição não deve reservar nada."""
    loteamento_b = await _criar_loteamento(rls_client, dois_tenants.token_b)
    lote_b = await _criar_lote(rls_client, dois_tenants.token_b, loteamento_b)

    response = await rls_client.post(
        "/reservas",
        json={"lote_id": lote_b, "cliente_id": dois_tenants.cliente_a},
        headers=_auth_headers(dois_tenants.token_b),
    )

    assert response.status_code == 404
    # O lote do tenant B não pode ter sido movido para RESERVADO por uma reserva rejeitada.
    lote_response = await rls_client.get(f"/lotes/{lote_b}", headers=_auth_headers(dois_tenants.token_b))
    assert lote_response.json()["status"] == "disponivel"


@pytest.mark.asyncio
async def test_criar_reserva_com_corretor_de_outro_tenant_retorna_404(
    rls_client: AsyncClient, dois_tenants: _DoisTenants
):
    """Forjar o `corretor_id` de outro tenant no corpo da requisição não deve reservar nada."""
    loteamento_b = await _criar_loteamento(rls_client, dois_tenants.token_b)
    lote_b = await _criar_lote(rls_client, dois_tenants.token_b, loteamento_b)
    cliente_b = await _criar_cliente(rls_client, dois_tenants.token_b)

    response = await rls_client.post(
        "/reservas",
        json={"lote_id": lote_b, "cliente_id": cliente_b, "corretor_id": dois_tenants.corretor_a},
        headers=_auth_headers(dois_tenants.token_b),
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_converter_venda_de_reserva_de_outro_tenant_retorna_404(
    rls_client: AsyncClient, dois_tenants: _DoisTenants
):
    response = await rls_client.post(
        f"/reservas/{dois_tenants.reserva_a['id']}/converter-venda",
        headers=_auth_headers(dois_tenants.token_b),
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cancelar_reserva_de_outro_tenant_retorna_404(rls_client: AsyncClient, dois_tenants: _DoisTenants):
    response = await rls_client.post(
        f"/reservas/{dois_tenants.reserva_a['id']}/cancelar",
        headers=_auth_headers(dois_tenants.token_b),
    )
    assert response.status_code == 404
