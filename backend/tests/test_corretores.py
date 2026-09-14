"""Tests for the corretores module (CRUD e remoção lógica)."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.identity.application.security import create_access_token, hash_password
from app.identity.domain.models import User, UserTenantMembership
from app.tenancy.domain.models import Tenant
from app.config import Settings


async def _criar_usuario_com_tenant(db: AsyncSession, tenant_slug: str) -> tuple[str, User]:
    """Cria um usuário com membership em um tenant e retorna (token, user)."""
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
    return token, user


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_criar_corretor(client: AsyncClient, db_session: AsyncSession):
    """Criar um corretor retorna 201 com os dados cadastrados."""
    token, _ = await _criar_usuario_com_tenant(db_session, "tenant-corretor-criar")

    response = await client.post(
        "/corretores",
        json={"nome": "Maria Corretora", "contato": "maria@email.com"},
        headers=_auth_headers(token),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["nome"] == "Maria Corretora"
    assert body["contato"] == "maria@email.com"
    assert body["usuario_id"] is None


@pytest.mark.asyncio
async def test_criar_corretor_com_usuario_associado(client: AsyncClient, db_session: AsyncSession):
    """Criar um corretor pode associar opcionalmente um usuário existente."""
    token, user = await _criar_usuario_com_tenant(db_session, "tenant-corretor-usuario")

    response = await client.post(
        "/corretores",
        json={"nome": "Corretor Usuário", "contato": "cu@email.com", "usuario_id": str(user.id)},
        headers=_auth_headers(token),
    )

    assert response.status_code == 201
    assert response.json()["usuario_id"] == str(user.id)


@pytest.mark.asyncio
async def test_listar_corretores_isola_por_tenant(client: AsyncClient, db_session: AsyncSession):
    """Um tenant não vê corretores cadastrados por outro tenant."""
    token_a, _ = await _criar_usuario_com_tenant(db_session, "tenant-corretor-a")
    token_b, _ = await _criar_usuario_com_tenant(db_session, "tenant-corretor-b")

    await client.post(
        "/corretores",
        json={"nome": "Corretor A", "contato": "a@email.com"},
        headers=_auth_headers(token_a),
    )

    response = await client.get("/corretores", headers=_auth_headers(token_b))

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_atualizar_corretor(client: AsyncClient, db_session: AsyncSession):
    """Atualizar um corretor altera somente os campos informados."""
    token, _ = await _criar_usuario_com_tenant(db_session, "tenant-corretor-atualizar")

    criado = await client.post(
        "/corretores",
        json={"nome": "Nome Antigo", "contato": "antigo@email.com"},
        headers=_auth_headers(token),
    )
    corretor_id = criado.json()["id"]

    response = await client.patch(
        f"/corretores/{corretor_id}",
        json={"nome": "Nome Novo"},
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["nome"] == "Nome Novo"
    assert body["contato"] == "antigo@email.com"


@pytest.mark.asyncio
async def test_remover_corretor_e_remocao_logica(client: AsyncClient, db_session: AsyncSession):
    """Remover um corretor é lógico: some da listagem mas não é hard-delete."""
    token, _ = await _criar_usuario_com_tenant(db_session, "tenant-corretor-remover")

    criado = await client.post(
        "/corretores",
        json={"nome": "Corretor Removido", "contato": "rem@email.com"},
        headers=_auth_headers(token),
    )
    corretor_id = criado.json()["id"]

    delete_response = await client.delete(f"/corretores/{corretor_id}", headers=_auth_headers(token))
    assert delete_response.status_code == 204

    get_response = await client.get(f"/corretores/{corretor_id}", headers=_auth_headers(token))
    assert get_response.status_code == 404

    list_response = await client.get("/corretores", headers=_auth_headers(token))
    assert list_response.json() == []


@pytest.mark.asyncio
async def test_obter_corretor_inexistente_retorna_404(client: AsyncClient, db_session: AsyncSession):
    """Buscar um corretor com id inexistente retorna 404."""
    token, _ = await _criar_usuario_com_tenant(db_session, "tenant-corretor-404")

    response = await client.get(
        "/corretores/00000000-0000-0000-0000-000000000000", headers=_auth_headers(token)
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_corretores_sem_token_retorna_401(client: AsyncClient):
    """Acesso a /corretores sem token retorna 401."""
    response = await client.get("/corretores")

    assert response.status_code == 401
