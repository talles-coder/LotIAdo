"""Tests for invitations and membership deactivation (SCRUM-59 / FASE2-IMPL-03)."""
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.identity.application.security import create_access_token, hash_password
from app.identity.domain.models import Invitation, User, UserTenantMembership
from app.tenancy.domain.models import Tenant


async def _criar_usuario_com_papel(db: AsyncSession, tenant_slug: str, role: str) -> tuple[str, User, Tenant]:
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

    token = create_access_token(user.id, tenant.id, Settings())
    return token, user, tenant


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_admin_convida_usuario_com_sucesso(client: AsyncClient, db_session: AsyncSession):
    """Um admin convida um e-mail para o tenant e recebe o token do convite na resposta."""
    token, _user, _tenant = await _criar_usuario_com_papel(db_session, "tenant-convite-sucesso", "admin")

    response = await client.post(
        "/auth/invitations",
        json={"email": "convidado@test.com", "role": "corretor"},
        headers=_auth_headers(token),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "convidado@test.com"
    assert body["role"] == "corretor"
    assert "token" in body and body["token"]
    assert "expires_at" in body


@pytest.mark.asyncio
async def test_convidar_sem_permissao_retorna_403(client: AsyncClient, db_session: AsyncSession):
    """Um corretor (sem 'usuarios:gerenciar') não pode convidar."""
    token, _user, _tenant = await _criar_usuario_com_papel(db_session, "tenant-convite-sem-permissao", "corretor")

    response = await client.post(
        "/auth/invitations",
        json={"email": "convidado@test.com", "role": "corretor"},
        headers=_auth_headers(token),
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_convidar_email_ja_ativo_no_tenant_retorna_409(client: AsyncClient, db_session: AsyncSession):
    """Convidar um e-mail que já é membro ativo do tenant é rejeitado."""
    token, _admin, tenant = await _criar_usuario_com_papel(db_session, "tenant-convite-duplicado", "admin")

    membro = User(email="ja-membro@test.com", hashed_password=hash_password("x"), full_name="Já Membro")
    db_session.add(membro)
    await db_session.flush()
    db_session.add(UserTenantMembership(user_id=membro.id, tenant_id=tenant.id, role="corretor"))
    await db_session.commit()

    response = await client.post(
        "/auth/invitations",
        json={"email": "ja-membro@test.com", "role": "corretor"},
        headers=_auth_headers(token),
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_convites_sem_token_retorna_401(client: AsyncClient):
    """Acesso a POST /auth/invitations sem token retorna 401."""
    response = await client.post("/auth/invitations", json={"email": "x@test.com", "role": "corretor"})

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_aceitar_convite_cria_usuario_e_membership_ativa(client: AsyncClient, db_session: AsyncSession):
    """Aceitar um convite cria o usuário, ativa a membership, e ele já consegue logar no tenant."""
    admin_token, _admin, tenant = await _criar_usuario_com_papel(db_session, "tenant-aceite-sucesso", "admin")

    convite = await client.post(
        "/auth/invitations",
        json={"email": "novo@test.com", "role": "corretor"},
        headers=_auth_headers(admin_token),
    )
    invitation_token = convite.json()["token"]

    aceite = await client.post(
        f"/auth/invitations/{invitation_token}/accept",
        json={"full_name": "Novo Corretor", "password": "senha123"},
    )

    assert aceite.status_code == 200
    body = aceite.json()
    assert body["email"] == "novo@test.com"
    assert body["full_name"] == "Novo Corretor"

    login = await client.post("/auth/login", json={"email": "novo@test.com", "password": "senha123"})
    assert login.status_code == 200
    login_token = login.json()["access_token"]

    me = await client.get("/auth/me", headers=_auth_headers(login_token))
    assert me.status_code == 200
    assert me.json()["tenant_id"] == str(tenant.id)


@pytest.mark.asyncio
async def test_aceitar_convite_token_invalido_retorna_404(client: AsyncClient):
    """Aceitar com um token que não corresponde a nenhum convite retorna 404."""
    response = await client.post(
        "/auth/invitations/token-invalido/accept",
        json={"full_name": "X", "password": "senha123"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_aceitar_convite_ja_aceito_retorna_409(client: AsyncClient, db_session: AsyncSession):
    """Um token de convite não é reutilizável depois de aceito (critério de aceite da SCRUM-59)."""
    admin_token, _admin, _tenant = await _criar_usuario_com_papel(db_session, "tenant-convite-reuso", "admin")

    convite = await client.post(
        "/auth/invitations",
        json={"email": "reuso@test.com", "role": "corretor"},
        headers=_auth_headers(admin_token),
    )
    invitation_token = convite.json()["token"]

    primeiro = await client.post(
        f"/auth/invitations/{invitation_token}/accept",
        json={"full_name": "Primeiro", "password": "senha123"},
    )
    assert primeiro.status_code == 200

    segundo = await client.post(
        f"/auth/invitations/{invitation_token}/accept",
        json={"full_name": "Segundo", "password": "outrasenha"},
    )
    assert segundo.status_code == 409


@pytest.mark.asyncio
async def test_aceitar_convite_expirado_retorna_409(client: AsyncClient, db_session: AsyncSession):
    """Um convite expirado (mesmo nunca usado) não pode mais ser aceito (critério de aceite da SCRUM-59)."""
    _admin_token, admin, tenant = await _criar_usuario_com_papel(db_session, "tenant-convite-expirado", "admin")

    invitation = Invitation(
        tenant_id=tenant.id,
        email="atrasado@test.com",
        role="corretor",
        token="token-ja-expirado",
        invited_by_user_id=admin.id,
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    db_session.add(invitation)
    await db_session.commit()

    response = await client.post(
        "/auth/invitations/token-ja-expirado/accept",
        json={"full_name": "Atrasado", "password": "senha123"},
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_desativar_membership_com_sucesso(client: AsyncClient, db_session: AsyncSession):
    """Desativar a membership de um usuário faz um token já emitido parar de funcionar no tenant."""
    admin_token, _admin, tenant = await _criar_usuario_com_papel(db_session, "tenant-desativar-sucesso", "admin")

    membro = User(email="alvo@test.com", hashed_password=hash_password("senha123"), full_name="Alvo")
    db_session.add(membro)
    await db_session.flush()
    membership = UserTenantMembership(user_id=membro.id, tenant_id=tenant.id, role="corretor")
    db_session.add(membership)
    await db_session.commit()

    membro_token = create_access_token(membro.id, tenant.id, Settings())
    antes = await client.get("/clientes", headers=_auth_headers(membro_token))
    assert antes.status_code == 200

    desativar = await client.post(
        f"/auth/memberships/{membership.id}/deactivate", headers=_auth_headers(admin_token)
    )
    assert desativar.status_code == 204

    result = await db_session.execute(
        select(UserTenantMembership).where(UserTenantMembership.id == membership.id)
    )
    assert result.scalar_one().is_active is False

    # O mesmo JWT, já emitido antes da desativação, para de funcionar no tenant
    # (get_current_tenant_id reconfere a membership no banco a cada request —
    # não basta o claim `tenant_id` do token ainda ser criptograficamente válido).
    depois = await client.get("/clientes", headers=_auth_headers(membro_token))
    assert depois.status_code == 401

    # Um novo login também não recupera acesso ao tenant: a membership segue
    # desativada, então `/auth/me` não resolve mais nenhum tenant_id para ele.
    novo_login = await client.post("/auth/login", json={"email": "alvo@test.com", "password": "senha123"})
    assert novo_login.status_code == 200
    novo_token = novo_login.json()["access_token"]
    me_depois_login = await client.get("/auth/me", headers=_auth_headers(novo_token))
    assert me_depois_login.json()["tenant_id"] is None


@pytest.mark.asyncio
async def test_desativar_sem_permissao_retorna_403(client: AsyncClient, db_session: AsyncSession):
    """Um corretor (sem 'usuarios:gerenciar') não pode desativar outra membership."""
    corretor_token, _corretor, tenant = await _criar_usuario_com_papel(
        db_session, "tenant-desativar-sem-permissao", "corretor"
    )

    membro = User(email="outro@test.com", hashed_password=hash_password("x"), full_name="Outro")
    db_session.add(membro)
    await db_session.flush()
    membership = UserTenantMembership(user_id=membro.id, tenant_id=tenant.id, role="corretor")
    db_session.add(membership)
    await db_session.commit()

    response = await client.post(
        f"/auth/memberships/{membership.id}/deactivate", headers=_auth_headers(corretor_token)
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_desativar_membership_de_outro_tenant_retorna_404(client: AsyncClient, db_session: AsyncSession):
    """Forjar o id de uma membership de outro tenant na URL não deve desativar nada."""
    admin_a_token, _admin_a, _tenant_a = await _criar_usuario_com_papel(
        db_session, "tenant-desativar-cross-a", "admin"
    )
    _admin_b_token, admin_b, tenant_b = await _criar_usuario_com_papel(
        db_session, "tenant-desativar-cross-b", "admin"
    )
    membership_b = await db_session.execute(
        select(UserTenantMembership).where(UserTenantMembership.user_id == admin_b.id)
    )
    membership_b_id = membership_b.scalar_one().id

    response = await client.post(
        f"/auth/memberships/{membership_b_id}/deactivate", headers=_auth_headers(admin_a_token)
    )

    assert response.status_code == 404

    result = await db_session.execute(
        select(UserTenantMembership).where(UserTenantMembership.id == membership_b_id)
    )
    assert result.scalar_one().is_active is True


@pytest.mark.asyncio
async def test_reconvidar_usuario_desativado_e_aceitar_reativa_a_membership(
    client: AsyncClient, db_session: AsyncSession
):
    """Reconvidar um e-mail cuja membership foi desativada funciona, e aceitar reativa a mesma membership."""
    admin_token, _admin, tenant = await _criar_usuario_com_papel(db_session, "tenant-reconvite", "admin")

    membro = User(email="reconvidado@test.com", hashed_password=hash_password("senha-antiga"), full_name="Antigo")
    db_session.add(membro)
    await db_session.flush()
    membership = UserTenantMembership(user_id=membro.id, tenant_id=tenant.id, role="corretor", is_active=False)
    db_session.add(membership)
    await db_session.commit()
    membership_id = membership.id

    convite = await client.post(
        "/auth/invitations",
        json={"email": "reconvidado@test.com", "role": "gestor"},
        headers=_auth_headers(admin_token),
    )
    assert convite.status_code == 201
    invitation_token = convite.json()["token"]

    aceite = await client.post(
        f"/auth/invitations/{invitation_token}/accept",
        json={"full_name": "Ignorado", "password": "senha-ignorada"},
    )
    assert aceite.status_code == 200

    result = await db_session.execute(
        select(UserTenantMembership).where(UserTenantMembership.id == membership_id)
    )
    membership_recarregada = result.scalar_one()
    assert membership_recarregada.is_active is True
    assert membership_recarregada.role == "gestor"

    login = await client.post("/auth/login", json={"email": "reconvidado@test.com", "password": "senha-antiga"})
    assert login.status_code == 200
    assert login.json()["access_token"]
