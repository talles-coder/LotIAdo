"""Testes de integração do módulo loteamentos_lotes (CRUD e transição de status)."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.identity.application.security import create_access_token, hash_password
from app.identity.domain.models import User, UserTenantMembership
from app.tenancy.domain.models import Tenant


async def _criar_usuario_com_tenant(db: AsyncSession, tenant_slug: str) -> str:
    """Cria um usuário com membership em um tenant e retorna o token JWT."""
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
    response = await client.post(
        "/loteamentos", json={"nome": nome}, headers=_auth_headers(token)
    )
    return response.json()["id"]


async def _criar_lote(client: AsyncClient, token: str, loteamento_id: str, identificacao: str = "Lote 1") -> dict:
    response = await client.post(
        f"/loteamentos/{loteamento_id}/lotes",
        json={"identificacao": identificacao},
        headers=_auth_headers(token),
    )
    return response.json()


@pytest.mark.asyncio
async def test_criar_e_obter_loteamento(client: AsyncClient, db_session: AsyncSession):
    """Criar um loteamento retorna 201 e ele pode ser recuperado depois."""
    token = await _criar_usuario_com_tenant(db_session, "tenant-loteamento-criar")

    criado = await client.post(
        "/loteamentos",
        json={"nome": "Residencial Sol Nascente", "descricao": "Fase 1"},
        headers=_auth_headers(token),
    )
    assert criado.status_code == 201
    loteamento_id = criado.json()["id"]

    obtido = await client.get(f"/loteamentos/{loteamento_id}", headers=_auth_headers(token))
    assert obtido.status_code == 200
    assert obtido.json()["nome"] == "Residencial Sol Nascente"


@pytest.mark.asyncio
async def test_listar_loteamentos_isola_por_tenant(client: AsyncClient, db_session: AsyncSession):
    """Um tenant não vê loteamentos cadastrados por outro tenant."""
    token_a = await _criar_usuario_com_tenant(db_session, "tenant-loteamento-a")
    token_b = await _criar_usuario_com_tenant(db_session, "tenant-loteamento-b")

    await _criar_loteamento(client, token_a)

    response = await client.get("/loteamentos", headers=_auth_headers(token_b))

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_atualizar_loteamento(client: AsyncClient, db_session: AsyncSession):
    """Atualizar um loteamento altera somente os campos informados."""
    token = await _criar_usuario_com_tenant(db_session, "tenant-loteamento-atualizar")
    loteamento_id = await _criar_loteamento(client, token, nome="Nome Antigo")

    response = await client.patch(
        f"/loteamentos/{loteamento_id}", json={"nome": "Nome Novo"}, headers=_auth_headers(token)
    )

    assert response.status_code == 200
    assert response.json()["nome"] == "Nome Novo"


@pytest.mark.asyncio
async def test_remover_loteamento_e_remocao_logica(client: AsyncClient, db_session: AsyncSession):
    """Remover um loteamento é lógico: some da listagem mas não é hard-delete."""
    token = await _criar_usuario_com_tenant(db_session, "tenant-loteamento-remover")
    loteamento_id = await _criar_loteamento(client, token)

    delete_response = await client.delete(f"/loteamentos/{loteamento_id}", headers=_auth_headers(token))
    assert delete_response.status_code == 204

    get_response = await client.get(f"/loteamentos/{loteamento_id}", headers=_auth_headers(token))
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_obter_loteamento_inexistente_retorna_404(client: AsyncClient, db_session: AsyncSession):
    """Buscar um loteamento com id inexistente retorna 404."""
    token = await _criar_usuario_com_tenant(db_session, "tenant-loteamento-404")

    response = await client.get(
        "/loteamentos/00000000-0000-0000-0000-000000000000", headers=_auth_headers(token)
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_criar_lote_em_loteamento_inexistente_retorna_404(client: AsyncClient, db_session: AsyncSession):
    """Criar um lote em um loteamento inexistente (ou de outro tenant) retorna 404."""
    token = await _criar_usuario_com_tenant(db_session, "tenant-lote-404")

    response = await client.post(
        "/loteamentos/00000000-0000-0000-0000-000000000000/lotes",
        json={"identificacao": "Lote 1"},
        headers=_auth_headers(token),
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_criar_lote_com_status_inicial_disponivel(client: AsyncClient, db_session: AsyncSession):
    """Um lote recém-criado começa com status DISPONIVEL."""
    token = await _criar_usuario_com_tenant(db_session, "tenant-lote-criar")
    loteamento_id = await _criar_loteamento(client, token)

    lote = await _criar_lote(client, token, loteamento_id)

    assert lote["status"] == "disponivel"
    assert lote["loteamento_id"] == loteamento_id


@pytest.mark.asyncio
async def test_listar_lotes_isola_por_tenant(client: AsyncClient, db_session: AsyncSession):
    """Um tenant não vê lotes cadastrados por outro tenant."""
    token_a = await _criar_usuario_com_tenant(db_session, "tenant-lote-a")
    token_b = await _criar_usuario_com_tenant(db_session, "tenant-lote-b")

    loteamento_a = await _criar_loteamento(client, token_a)
    await _criar_lote(client, token_a, loteamento_a)

    loteamento_b = await _criar_loteamento(client, token_b)
    response = await client.get(f"/loteamentos/{loteamento_b}/lotes", headers=_auth_headers(token_b))

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_atualizar_lote(client: AsyncClient, db_session: AsyncSession):
    """Atualizar um lote altera somente os campos informados, sem tocar o status."""
    token = await _criar_usuario_com_tenant(db_session, "tenant-lote-atualizar")
    loteamento_id = await _criar_loteamento(client, token)
    lote = await _criar_lote(client, token, loteamento_id)

    response = await client.patch(
        f"/lotes/{lote['id']}", json={"preco": "150000.00"}, headers=_auth_headers(token)
    )

    assert response.status_code == 200
    body = response.json()
    assert body["preco"] == "150000.00"
    assert body["status"] == "disponivel"


@pytest.mark.asyncio
async def test_transicao_de_status_valida(client: AsyncClient, db_session: AsyncSession):
    """Transição permitida (DISPONIVEL -> RESERVADO) é aplicada e retorna 200."""
    token = await _criar_usuario_com_tenant(db_session, "tenant-lote-transicao-valida")
    loteamento_id = await _criar_loteamento(client, token)
    lote = await _criar_lote(client, token, loteamento_id)

    response = await client.patch(
        f"/lotes/{lote['id']}/status", json={"status": "reservado"}, headers=_auth_headers(token)
    )

    assert response.status_code == 200
    assert response.json()["status"] == "reservado"


@pytest.mark.asyncio
async def test_transicao_de_status_invalida_retorna_409(client: AsyncClient, db_session: AsyncSession):
    """Transição proibida (DISPONIVEL -> VENDIDO) retorna 409 com mensagem clara."""
    token = await _criar_usuario_com_tenant(db_session, "tenant-lote-transicao-invalida")
    loteamento_id = await _criar_loteamento(client, token)
    lote = await _criar_lote(client, token, loteamento_id)

    response = await client.patch(
        f"/lotes/{lote['id']}/status", json={"status": "vendido"}, headers=_auth_headers(token)
    )

    assert response.status_code == 409
    assert "disponivel" in response.json()["detail"]
    assert "vendido" in response.json()["detail"]


@pytest.mark.asyncio
async def test_remover_lote_e_remocao_logica(client: AsyncClient, db_session: AsyncSession):
    """Remover um lote é lógico: some da listagem mas não é hard-delete."""
    token = await _criar_usuario_com_tenant(db_session, "tenant-lote-remover")
    loteamento_id = await _criar_loteamento(client, token)
    lote = await _criar_lote(client, token, loteamento_id)

    delete_response = await client.delete(f"/lotes/{lote['id']}", headers=_auth_headers(token))
    assert delete_response.status_code == 204

    get_response = await client.get(f"/lotes/{lote['id']}", headers=_auth_headers(token))
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_loteamentos_sem_token_retorna_401(client: AsyncClient):
    """Acesso a /loteamentos sem token retorna 401."""
    response = await client.get("/loteamentos")

    assert response.status_code == 401
