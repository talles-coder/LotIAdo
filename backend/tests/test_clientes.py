"""Tests for the clientes module (CRUD e remoção lógica)."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.identity.application.security import create_access_token, hash_password
from app.identity.domain.models import User, UserTenantMembership
from app.tenancy.domain.models import Tenant
from app.config import Settings


async def _criar_usuario_com_tenant(db: AsyncSession, tenant_slug: str) -> tuple[str, object]:
    """Cria um usuário com membership em um tenant e retorna (token, tenant)."""
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

    token = create_access_token(user.id, tenant.id, Settings())
    return token, tenant


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_criar_cliente(client: AsyncClient, db_session: AsyncSession):
    """Criar um cliente retorna 201 com os dados cadastrados."""
    token, _ = await _criar_usuario_com_tenant(db_session, "tenant-cliente-criar")

    response = await client.post(
        "/clientes",
        json={"nome": "João da Silva", "documento": "12345678900", "contato": "joao@email.com"},
        headers=_auth_headers(token),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["nome"] == "João da Silva"
    assert body["documento"] == "12345678900"
    assert body["contato"] == "joao@email.com"


@pytest.mark.asyncio
async def test_listar_clientes(client: AsyncClient, db_session: AsyncSession):
    """Listar clientes retorna somente os clientes ativos do tenant autenticado."""
    token, _ = await _criar_usuario_com_tenant(db_session, "tenant-cliente-listar")

    await client.post(
        "/clientes",
        json={"nome": "Cliente 1", "documento": "111", "contato": "c1@email.com"},
        headers=_auth_headers(token),
    )
    await client.post(
        "/clientes",
        json={"nome": "Cliente 2", "documento": "222", "contato": "c2@email.com"},
        headers=_auth_headers(token),
    )

    response = await client.get("/clientes", headers=_auth_headers(token))

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2


@pytest.mark.asyncio
async def test_listar_clientes_isola_por_tenant(client: AsyncClient, db_session: AsyncSession):
    """Um tenant não vê clientes cadastrados por outro tenant."""
    token_a, _ = await _criar_usuario_com_tenant(db_session, "tenant-cliente-a")
    token_b, _ = await _criar_usuario_com_tenant(db_session, "tenant-cliente-b")

    await client.post(
        "/clientes",
        json={"nome": "Cliente A", "documento": "111", "contato": "a@email.com"},
        headers=_auth_headers(token_a),
    )

    response = await client.get("/clientes", headers=_auth_headers(token_b))

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_atualizar_cliente(client: AsyncClient, db_session: AsyncSession):
    """Atualizar um cliente altera somente os campos informados."""
    token, _ = await _criar_usuario_com_tenant(db_session, "tenant-cliente-atualizar")

    criado = await client.post(
        "/clientes",
        json={"nome": "Nome Antigo", "documento": "999", "contato": "antigo@email.com"},
        headers=_auth_headers(token),
    )
    cliente_id = criado.json()["id"]

    response = await client.patch(
        f"/clientes/{cliente_id}",
        json={"nome": "Nome Novo"},
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["nome"] == "Nome Novo"
    assert body["documento"] == "999"


@pytest.mark.asyncio
async def test_remover_cliente_e_remocao_logica(client: AsyncClient, db_session: AsyncSession):
    """Remover um cliente é lógico: some da listagem mas não é hard-delete."""
    token, _ = await _criar_usuario_com_tenant(db_session, "tenant-cliente-remover")

    criado = await client.post(
        "/clientes",
        json={"nome": "Cliente Removido", "documento": "555", "contato": "rem@email.com"},
        headers=_auth_headers(token),
    )
    cliente_id = criado.json()["id"]

    delete_response = await client.delete(f"/clientes/{cliente_id}", headers=_auth_headers(token))
    assert delete_response.status_code == 204

    get_response = await client.get(f"/clientes/{cliente_id}", headers=_auth_headers(token))
    assert get_response.status_code == 404

    list_response = await client.get("/clientes", headers=_auth_headers(token))
    assert list_response.json() == []


@pytest.mark.asyncio
async def test_obter_cliente_inexistente_retorna_404(client: AsyncClient, db_session: AsyncSession):
    """Buscar um cliente com id inexistente retorna 404."""
    token, _ = await _criar_usuario_com_tenant(db_session, "tenant-cliente-404")

    response = await client.get(
        "/clientes/00000000-0000-0000-0000-000000000000", headers=_auth_headers(token)
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_clientes_sem_token_retorna_401(client: AsyncClient):
    """Acesso a /clientes sem token retorna 401."""
    response = await client.get("/clientes")

    assert response.status_code == 401
