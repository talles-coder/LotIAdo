"""Tests for the identity module (login and /auth/me)."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.identity.application.security import hash_password
from app.identity.domain.models import User, UserTenantMembership
from app.tenancy.domain.models import Tenant


async def _create_user_with_membership(
    db: AsyncSession, email: str, password: str, tenant_slug: str
) -> tuple[User, Tenant]:
    tenant = Tenant(name=tenant_slug, slug=tenant_slug)
    db.add(tenant)
    await db.flush()

    user = User(email=email, hashed_password=hash_password(password), full_name="Test User")
    db.add(user)
    await db.flush()

    db.add(UserTenantMembership(user_id=user.id, tenant_id=tenant.id, role="admin"))
    await db.commit()

    return user, tenant


@pytest.mark.asyncio
async def test_login_com_sucesso(client: AsyncClient, db_session: AsyncSession):
    """Login com credenciais corretas retorna um JWT."""
    await _create_user_with_membership(db_session, "user@test.com", "senha123", "tenant-login")

    response = await client.post(
        "/auth/login", json={"email": "user@test.com", "password": "senha123"}
    )

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_com_senha_errada_retorna_401(client: AsyncClient, db_session: AsyncSession):
    """Login com senha incorreta retorna 401."""
    await _create_user_with_membership(db_session, "user2@test.com", "senha123", "tenant-wrong-pw")

    response = await client.post(
        "/auth/login", json={"email": "user2@test.com", "password": "senha-errada"}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_usuario_inexistente_retorna_401(client: AsyncClient):
    """Login com email não cadastrado retorna 401."""
    response = await client.post(
        "/auth/login", json={"email": "naoexiste@test.com", "password": "qualquer"}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_sem_token_retorna_401(client: AsyncClient):
    """Acesso a /auth/me sem token retorna 401."""
    response = await client.get("/auth/me")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_com_token_retorna_usuario_e_tenant(client: AsyncClient, db_session: AsyncSession):
    """Acesso a /auth/me autenticado retorna o usuário e seu tenant."""
    user, tenant = await _create_user_with_membership(
        db_session, "user3@test.com", "senha123", "tenant-me"
    )

    login_response = await client.post(
        "/auth/login", json={"email": "user3@test.com", "password": "senha123"}
    )
    token = login_response.json()["access_token"]

    response = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(user.id)
    assert body["email"] == "user3@test.com"
    assert body["tenant_id"] == str(tenant.id)
