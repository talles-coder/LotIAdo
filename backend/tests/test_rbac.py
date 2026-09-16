"""Tests for permission-based RBAC (SCRUM-60 / FASE2-IMPL-04)."""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.identity.application.security import create_access_token, hash_password
from app.identity.domain.models import Permission, RolePermission, User, UserTenantMembership
from app.tenancy.domain.models import Tenant


async def _conceder_permissao(db: AsyncSession, role: str, permission_key: str) -> None:
    """Concede uma permissão já seedada (ver conftest.PERMISSOES_SEED) a um papel."""
    result = await db.execute(select(Permission).where(Permission.key == permission_key))
    permissao = result.scalar_one()
    db.add(RolePermission(role=role, permission_id=permissao.id))
    await db.commit()


async def _criar_usuario_com_papel(db: AsyncSession, tenant_slug: str, role: str) -> str:
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

    db.add(UserTenantMembership(user_id=user.id, tenant_id=tenant.id, role=role))
    await db.commit()

    return create_access_token(user.id, tenant.id, Settings())


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_papel_sem_permissao_recebe_403(client: AsyncClient, db_session: AsyncSession):
    """Um papel sem a permissão 'clientes:gerenciar' não pode criar clientes."""
    token = await _criar_usuario_com_papel(db_session, "tenant-rbac-sem-permissao", "estagiario")

    response = await client.post(
        "/clientes",
        json={"nome": "Cliente Teste", "documento": "123", "contato": "contato"},
        headers=_auth_headers(token),
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_papel_customizado_com_permissao_concedida_funciona(
    client: AsyncClient, db_session: AsyncSession
):
    """Criar um papel customizado via seed e conceder uma permissão a ele funciona
    sem qualquer alteração no código de rota (critério de aceite da SCRUM-60)."""
    await _conceder_permissao(db_session, "financeiro", "clientes:gerenciar")

    token = await _criar_usuario_com_papel(db_session, "tenant-rbac-papel-customizado", "financeiro")

    response = await client.post(
        "/clientes",
        json={"nome": "Cliente Teste", "documento": "123", "contato": "contato"},
        headers=_auth_headers(token),
    )

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_papel_customizado_sem_permissao_correspondente_recebe_403(
    client: AsyncClient, db_session: AsyncSession
):
    """Um papel customizado só recebe exatamente as permissões concedidas a ele:
    conceder 'corretores:gerenciar' não implica acesso a 'clientes:gerenciar'."""
    await _conceder_permissao(db_session, "financeiro", "corretores:gerenciar")

    token = await _criar_usuario_com_papel(db_session, "tenant-rbac-papel-parcial", "financeiro")

    response = await client.post(
        "/clientes",
        json={"nome": "Cliente Teste", "documento": "123", "contato": "contato"},
        headers=_auth_headers(token),
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_usuario_sem_membership_no_tenant_recebe_403(
    client: AsyncClient, db_session: AsyncSession
):
    """Um token com tenant_id sem membership correspondente é rejeitado."""
    tenant = Tenant(name="tenant-rbac-sem-membership", slug="tenant-rbac-sem-membership")
    db_session.add(tenant)
    await db_session.flush()

    user = User(
        email="sem-membership@test.com",
        hashed_password=hash_password("senha123"),
        full_name="Test User",
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.commit()

    token = create_access_token(user.id, tenant.id, Settings())

    response = await client.post(
        "/clientes",
        json={"nome": "Cliente Teste", "documento": "123", "contato": "contato"},
        headers=_auth_headers(token),
    )

    assert response.status_code == 403
