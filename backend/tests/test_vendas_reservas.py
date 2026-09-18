"""Testes de integração do módulo vendas_reservas (reservar, converter em venda, cancelar)."""
import asyncio

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.audit.domain.acoes import AcaoAuditoria
from app.audit.domain.models import AuditLog
from app.audit.infrastructure.context import contexto_auditoria
from app.clientes.domain.models import Cliente
from app.config import Settings
from app.identity.application.security import create_access_token, hash_password
from app.identity.domain.models import User, UserTenantMembership
from app.loteamentos_lotes.domain.models import Lote, Loteamento
from app.tenancy.domain.models import Tenant
from app.vendas_reservas.application.reserva_service import ReservaService
from app.vendas_reservas.domain.exceptions import LoteNaoDisponivelParaReservaError
from app.vendas_reservas.domain.models import ReservaVenda


async def _criar_usuario_com_tenant(db: AsyncSession, tenant_slug: str) -> tuple[str, User, Tenant]:
    """Cria um usuário com membership em um tenant e retorna (token, user, tenant)."""
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
    return token, user, tenant


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _criar_lote(client: AsyncClient, token: str) -> str:
    loteamento = await client.post(
        "/loteamentos", json={"nome": "Loteamento Teste"}, headers=_auth_headers(token)
    )
    loteamento_id = loteamento.json()["id"]

    lote = await client.post(
        f"/loteamentos/{loteamento_id}/lotes",
        json={"identificacao": "Lote 1"},
        headers=_auth_headers(token),
    )
    return lote.json()["id"]


async def _criar_cliente(client: AsyncClient, token: str) -> str:
    response = await client.post(
        "/clientes",
        json={"nome": "Cliente Teste", "documento": "12345678900", "contato": "cliente@test.com"},
        headers=_auth_headers(token),
    )
    return response.json()["id"]


async def _criar_reserva(client: AsyncClient, token: str, lote_id: str, cliente_id: str) -> dict:
    response = await client.post(
        "/reservas",
        json={"lote_id": lote_id, "cliente_id": cliente_id},
        headers=_auth_headers(token),
    )
    return response.json()


@pytest.mark.asyncio
async def test_criar_reserva_com_sucesso_move_o_lote_para_reservado(
    client: AsyncClient, db_session: AsyncSession
):
    """Reservar um lote disponível cria a reserva e move o lote para RESERVADO."""
    token, _user, _tenant = await _criar_usuario_com_tenant(db_session, "tenant-reserva-sucesso")
    lote_id = await _criar_lote(client, token)
    cliente_id = await _criar_cliente(client, token)

    response = await client.post(
        "/reservas", json={"lote_id": lote_id, "cliente_id": cliente_id}, headers=_auth_headers(token)
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "reservado"
    assert body["tipo"] == "reserva"
    assert body["lote_id"] == lote_id
    assert body["cliente_id"] == cliente_id

    lote_response = await client.get(f"/lotes/{lote_id}", headers=_auth_headers(token))
    assert lote_response.json()["status"] == "reservado"


@pytest.mark.asyncio
async def test_criar_reserva_em_lote_ja_reservado_retorna_409_e_nao_cria_segunda_reserva(
    client: AsyncClient, db_session: AsyncSession
):
    """Reservar um lote já reservado retorna 409 e não persiste uma segunda reserva (atomicidade)."""
    token, _user, _tenant = await _criar_usuario_com_tenant(db_session, "tenant-reserva-duplicada")
    lote_id = await _criar_lote(client, token)
    cliente_id = await _criar_cliente(client, token)

    await _criar_reserva(client, token, lote_id, cliente_id)

    response = await client.post(
        "/reservas", json={"lote_id": lote_id, "cliente_id": cliente_id}, headers=_auth_headers(token)
    )
    assert response.status_code == 409

    result = await db_session.execute(select(ReservaVenda).where(ReservaVenda.lote_id == lote_id))
    assert len(result.scalars().all()) == 1


@pytest.mark.asyncio
async def test_criar_reserva_em_lote_vendido_retorna_409(client: AsyncClient, db_session: AsyncSession):
    """Reservar um lote já vendido retorna 409."""
    token, _user, _tenant = await _criar_usuario_com_tenant(db_session, "tenant-reserva-vendido")
    lote_id = await _criar_lote(client, token)
    cliente_id = await _criar_cliente(client, token)

    reserva = await _criar_reserva(client, token, lote_id, cliente_id)
    await client.post(f"/reservas/{reserva['id']}/converter-venda", headers=_auth_headers(token))

    response = await client.post(
        "/reservas", json={"lote_id": lote_id, "cliente_id": cliente_id}, headers=_auth_headers(token)
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_criar_reserva_com_lote_inexistente_retorna_404(client: AsyncClient, db_session: AsyncSession):
    """Reservar um lote inexistente (ou de outro tenant) retorna 404."""
    token, _user, _tenant = await _criar_usuario_com_tenant(db_session, "tenant-reserva-404")
    cliente_id = await _criar_cliente(client, token)

    response = await client.post(
        "/reservas",
        json={"lote_id": "00000000-0000-0000-0000-000000000000", "cliente_id": cliente_id},
        headers=_auth_headers(token),
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_converter_para_venda_com_sucesso_move_o_lote_para_vendido(
    client: AsyncClient, db_session: AsyncSession
):
    """Converter uma reserva ativa em venda move o lote para VENDIDO."""
    token, _user, _tenant = await _criar_usuario_com_tenant(db_session, "tenant-venda-sucesso")
    lote_id = await _criar_lote(client, token)
    cliente_id = await _criar_cliente(client, token)
    reserva = await _criar_reserva(client, token, lote_id, cliente_id)

    response = await client.post(
        f"/reservas/{reserva['id']}/converter-venda", headers=_auth_headers(token)
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "vendido"
    assert body["tipo"] == "venda"

    lote_response = await client.get(f"/lotes/{lote_id}", headers=_auth_headers(token))
    assert lote_response.json()["status"] == "vendido"


@pytest.mark.asyncio
async def test_converter_para_venda_de_reserva_ja_cancelada_retorna_409(
    client: AsyncClient, db_session: AsyncSession
):
    """Converter em venda uma reserva que já foi cancelada retorna 409."""
    token, _user, _tenant = await _criar_usuario_com_tenant(db_session, "tenant-venda-cancelada")
    lote_id = await _criar_lote(client, token)
    cliente_id = await _criar_cliente(client, token)
    reserva = await _criar_reserva(client, token, lote_id, cliente_id)
    await client.post(f"/reservas/{reserva['id']}/cancelar", headers=_auth_headers(token))

    response = await client.post(
        f"/reservas/{reserva['id']}/converter-venda", headers=_auth_headers(token)
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_cancelar_reserva_com_sucesso_devolve_o_lote_para_disponivel(
    client: AsyncClient, db_session: AsyncSession
):
    """Cancelar uma reserva ativa devolve o lote para DISPONIVEL."""
    token, _user, _tenant = await _criar_usuario_com_tenant(db_session, "tenant-cancelar-sucesso")
    lote_id = await _criar_lote(client, token)
    cliente_id = await _criar_cliente(client, token)
    reserva = await _criar_reserva(client, token, lote_id, cliente_id)

    response = await client.post(f"/reservas/{reserva['id']}/cancelar", headers=_auth_headers(token))

    assert response.status_code == 200
    assert response.json()["status"] == "cancelada"

    lote_response = await client.get(f"/lotes/{lote_id}", headers=_auth_headers(token))
    assert lote_response.json()["status"] == "disponivel"


@pytest.mark.asyncio
async def test_cancelar_reserva_ja_vendida_retorna_409(client: AsyncClient, db_session: AsyncSession):
    """Cancelar uma reserva que já virou venda retorna 409."""
    token, _user, _tenant = await _criar_usuario_com_tenant(db_session, "tenant-cancelar-vendida")
    lote_id = await _criar_lote(client, token)
    cliente_id = await _criar_cliente(client, token)
    reserva = await _criar_reserva(client, token, lote_id, cliente_id)
    await client.post(f"/reservas/{reserva['id']}/converter-venda", headers=_auth_headers(token))

    response = await client.post(f"/reservas/{reserva['id']}/cancelar", headers=_auth_headers(token))
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_obter_reserva_ativa_por_lote_retorna_a_reserva_em_aberto(
    client: AsyncClient, db_session: AsyncSession
):
    """A reserva ativa de um lote reservado é encontrada por lote_id."""
    token, _user, _tenant = await _criar_usuario_com_tenant(db_session, "tenant-ativa-por-lote")
    lote_id = await _criar_lote(client, token)
    cliente_id = await _criar_cliente(client, token)
    reserva = await _criar_reserva(client, token, lote_id, cliente_id)

    response = await client.get(f"/reservas/ativa-por-lote/{lote_id}", headers=_auth_headers(token))

    assert response.status_code == 200
    assert response.json()["id"] == reserva["id"]
    assert response.json()["status"] == "reservado"


@pytest.mark.asyncio
async def test_obter_reserva_ativa_por_lote_sem_reserva_retorna_404(
    client: AsyncClient, db_session: AsyncSession
):
    """Um lote disponível (sem reserva ativa) retorna 404."""
    token, _user, _tenant = await _criar_usuario_com_tenant(db_session, "tenant-sem-reserva-ativa")
    lote_id = await _criar_lote(client, token)

    response = await client.get(f"/reservas/ativa-por-lote/{lote_id}", headers=_auth_headers(token))

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_obter_reserva_ativa_por_lote_apos_cancelamento_retorna_404(
    client: AsyncClient, db_session: AsyncSession
):
    """Após cancelar a reserva, o lote deixa de ter uma reserva ativa."""
    token, _user, _tenant = await _criar_usuario_com_tenant(db_session, "tenant-ativa-cancelada")
    lote_id = await _criar_lote(client, token)
    cliente_id = await _criar_cliente(client, token)
    reserva = await _criar_reserva(client, token, lote_id, cliente_id)
    await client.post(f"/reservas/{reserva['id']}/cancelar", headers=_auth_headers(token))

    response = await client.get(f"/reservas/ativa-por-lote/{lote_id}", headers=_auth_headers(token))

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_reservas_sem_token_retorna_401(client: AsyncClient):
    """Acesso a /reservas sem token retorna 401."""
    response = await client.post("/reservas", json={"lote_id": "x", "cliente_id": "y"})

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_criar_reserva_gera_uma_entrada_de_auditoria_para_lote_e_para_reserva(
    client: AsyncClient, db_session: AsyncSession
):
    """Criar uma reserva gera exatamente uma entrada de auditoria para o lote (transição) e uma para a reserva (criação)."""
    token, user, tenant = await _criar_usuario_com_tenant(db_session, "tenant-auditoria-criacao")
    lote_id = await _criar_lote(client, token)
    cliente_id = await _criar_cliente(client, token)

    reserva = await _criar_reserva(client, token, lote_id, cliente_id)

    lote_entries = (
        await db_session.execute(select(AuditLog).where(AuditLog.entidade_id == lote_id))
    ).scalars().all()
    reserva_entries = (
        await db_session.execute(select(AuditLog).where(AuditLog.entidade_id == reserva["id"]))
    ).scalars().all()

    assert len(lote_entries) == 1
    assert lote_entries[0].acao == AcaoAuditoria.TRANSICAO_STATUS
    assert lote_entries[0].tenant_id == tenant.id
    assert lote_entries[0].usuario_id == user.id

    assert len(reserva_entries) == 1
    assert reserva_entries[0].acao == AcaoAuditoria.CRIACAO_RESERVA
    assert reserva_entries[0].payload_depois["status"] == "reservado"


@pytest.mark.asyncio
async def test_converter_venda_gera_entrada_de_auditoria_de_venda(
    client: AsyncClient, db_session: AsyncSession
):
    """Converter em venda gera uma entrada de auditoria `venda` para a reserva."""
    token, _user, _tenant = await _criar_usuario_com_tenant(db_session, "tenant-auditoria-venda")
    lote_id = await _criar_lote(client, token)
    cliente_id = await _criar_cliente(client, token)
    reserva = await _criar_reserva(client, token, lote_id, cliente_id)

    await client.post(f"/reservas/{reserva['id']}/converter-venda", headers=_auth_headers(token))

    entries = (
        await db_session.execute(
            select(AuditLog).where(
                AuditLog.entidade_id == reserva["id"], AuditLog.acao == AcaoAuditoria.VENDA
            )
        )
    ).scalars().all()
    assert len(entries) == 1
    assert entries[0].payload_antes == {"status": "reservado"}
    assert entries[0].payload_depois == {"status": "vendido"}


@pytest.mark.asyncio
async def test_cancelar_gera_entrada_de_auditoria_de_cancelamento(
    client: AsyncClient, db_session: AsyncSession
):
    """Cancelar gera uma entrada de auditoria `cancelamento_reserva` para a reserva."""
    token, _user, _tenant = await _criar_usuario_com_tenant(db_session, "tenant-auditoria-cancelamento")
    lote_id = await _criar_lote(client, token)
    cliente_id = await _criar_cliente(client, token)
    reserva = await _criar_reserva(client, token, lote_id, cliente_id)

    await client.post(f"/reservas/{reserva['id']}/cancelar", headers=_auth_headers(token))

    entries = (
        await db_session.execute(
            select(AuditLog).where(
                AuditLog.entidade_id == reserva["id"],
                AuditLog.acao == AcaoAuditoria.CANCELAMENTO_RESERVA,
            )
        )
    ).scalars().all()
    assert len(entries) == 1
    assert entries[0].payload_depois == {"status": "cancelada"}


@pytest.mark.asyncio
async def test_duas_reservas_simultaneas_no_mesmo_lote_apenas_uma_sucede(async_engine):
    """Concorrência básica: duas tentativas simultâneas de reservar o mesmo lote — só uma pode vencer.

    Usa duas `AsyncSession` independentes (conexões reais separadas) sobre o
    mesmo engine, para que o `SELECT ... FOR UPDATE` de uma tentativa
    realmente bloqueie a outra até a primeira transação commitar — não
    apenas simule concorrência dentro de uma única sessão.
    """
    session_maker = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

    async with session_maker() as setup:
        _token, user, tenant = await _criar_usuario_com_tenant(setup, "tenant-concorrencia")

        loteamento = Loteamento(tenant_id=tenant.id, nome="Loteamento Concorrência")
        setup.add(loteamento)
        await setup.flush()

        lote = Lote(tenant_id=tenant.id, loteamento_id=loteamento.id, identificacao="Lote 1")
        setup.add(lote)

        cliente = Cliente(tenant_id=tenant.id, nome="Cliente", documento="1", contato="c@test.com")
        setup.add(cliente)
        await setup.commit()

        tenant_id, user_id, cliente_id, lote_id = tenant.id, user.id, cliente.id, lote.id

    async def _tentar_reservar():
        async with session_maker() as session:
            with contexto_auditoria(usuario_id=user_id, tenant_id=tenant_id):
                service = ReservaService(session)
                return await service.criar_reserva(tenant_id, lote_id, cliente_id)

    resultados = await asyncio.gather(_tentar_reservar(), _tentar_reservar(), return_exceptions=True)

    sucessos = [r for r in resultados if isinstance(r, ReservaVenda)]
    falhas = [r for r in resultados if isinstance(r, LoteNaoDisponivelParaReservaError)]

    assert len(sucessos) == 1
    assert len(falhas) == 1
