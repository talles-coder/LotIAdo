"""Testes do human-in-the-loop antes de tools de ação (FASE9-IMPL-03/SCRUM-105).

O LLM (`ai_rag.llm_provider.chat`) é mockado — o que se testa é o grafo do
agente nunca executar uma tool de ação sem uma pausa de confirmação
explícita, e a ação (quando aprovada) gerar auditoria marcada com origem
"agente".
"""
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.ai_rag as ai_rag
from app.ai_agents.application.agente_service import AgenteService
from app.ai_agents.domain.exceptions import ConfirmacaoNaoEncontradaError
from app.ai_rag.infrastructure.llm_provider import ChatResposta, ToolCall
from app.audit.domain.acoes import AcaoAuditoria
from app.audit.domain.models import AuditLog
from app.audit.infrastructure.context import contexto_auditoria
from app.clientes.domain.models import Cliente
from app.identity.application.security import hash_password
from app.identity.domain.models import User
from app.loteamentos_lotes.domain.models import Lote, Loteamento
from app.loteamentos_lotes.domain.state_machine import LoteStatus
from app.tenancy.domain.models import Tenant
from app.vendas_reservas.domain.models import ReservaVenda, StatusReservaVenda, TipoReservaVenda


async def _cenario_com_reserva(db: AsyncSession, slug: str):
    tenant = Tenant(name=slug, slug=slug)
    db.add(tenant)
    await db.flush()
    usuario = User(email=f"{slug}@test.com", hashed_password=hash_password("senha123"), full_name="Test User")
    db.add(usuario)
    await db.flush()
    loteamento = Loteamento(tenant_id=tenant.id, nome="Loteamento Teste")
    db.add(loteamento)
    await db.flush()
    lote = Lote(tenant_id=tenant.id, loteamento_id=loteamento.id, identificacao="L1", status=LoteStatus.RESERVADO)
    cliente = Cliente(tenant_id=tenant.id, nome="Maria", documento="123", contato="maria@test.com")
    db.add_all([lote, cliente])
    await db.flush()
    with contexto_auditoria(usuario_id=usuario.id, tenant_id=tenant.id):
        reserva = ReservaVenda(
            tenant_id=tenant.id, lote_id=lote.id, cliente_id=cliente.id,
            tipo=TipoReservaVenda.RESERVA, status=StatusReservaVenda.RESERVADO,
        )
        db.add(reserva)
        await db.commit()
    return tenant, usuario, reserva


def _mock_llm_propoe_cancelamento(reserva_id, mensagem_final: str) -> AsyncMock:
    mock_llm = AsyncMock()
    mock_llm.chat.side_effect = [
        ChatResposta(
            conteudo=None,
            tool_calls=[ToolCall(id="1", nome="cancelar_reserva", argumentos={"reserva_id": str(reserva_id)})],
        ),
        ChatResposta(conteudo=mensagem_final, tool_calls=[]),
    ]
    return mock_llm


@pytest.mark.asyncio
async def test_pedido_de_acao_pausa_para_confirmacao_sem_executar_a_tool(db_session: AsyncSession, monkeypatch):
    tenant, usuario, reserva = await _cenario_com_reserva(db_session, "confirmacao-pausa")
    monkeypatch.setattr(ai_rag, "llm_provider", _mock_llm_propoe_cancelamento(reserva.id, "não deveria chegar aqui"))

    service = AgenteService(db_session)
    with contexto_auditoria(usuario_id=usuario.id, tenant_id=tenant.id):
        resultado = await service.perguntar(tenant.id, "cancele a reserva do lote L1")

    assert resultado.resposta is None
    assert resultado.confirmacao is not None
    assert resultado.confirmacao.tool == "cancelar_reserva"
    assert resultado.confirmacao.argumentos == {"reserva_id": str(reserva.id)}
    # só uma chamada ao LLM: o grafo pausou antes de decidir de novo (a tool nunca rodou)
    assert ai_rag.llm_provider.chat.call_count == 1

    await db_session.refresh(reserva)
    assert reserva.status == StatusReservaVenda.RESERVADO


@pytest.mark.asyncio
async def test_acao_aprovada_executa_e_audita_com_origem_agente(db_session: AsyncSession, monkeypatch):
    tenant, usuario, reserva = await _cenario_com_reserva(db_session, "confirmacao-aprovada")
    monkeypatch.setattr(
        ai_rag, "llm_provider", _mock_llm_propoe_cancelamento(reserva.id, "Reserva cancelada com sucesso.")
    )

    service = AgenteService(db_session)
    with contexto_auditoria(usuario_id=usuario.id, tenant_id=tenant.id):
        pendente = await service.perguntar(tenant.id, "cancele a reserva do lote L1")
        resultado = await service.confirmar(tenant.id, pendente.confirmacao.confirmacao_id, aprovado=True)

    assert resultado.resposta == "Reserva cancelada com sucesso."
    assert resultado.confirmacao is None
    await db_session.refresh(reserva)
    assert reserva.status == StatusReservaVenda.CANCELADA

    entrada = (
        await db_session.execute(
            select(AuditLog).where(
                AuditLog.entidade_id == reserva.id, AuditLog.acao == AcaoAuditoria.CANCELAMENTO_RESERVA
            )
        )
    ).scalar_one()
    assert entrada.usuario_id == usuario.id
    assert entrada.payload_depois["origem"] == "agente"


@pytest.mark.asyncio
async def test_acao_recusada_nao_executa_a_tool(db_session: AsyncSession, monkeypatch):
    tenant, usuario, reserva = await _cenario_com_reserva(db_session, "confirmacao-recusada")
    monkeypatch.setattr(ai_rag, "llm_provider", _mock_llm_propoe_cancelamento(reserva.id, "Ok, mantive a reserva."))

    service = AgenteService(db_session)
    with contexto_auditoria(usuario_id=usuario.id, tenant_id=tenant.id):
        pendente = await service.perguntar(tenant.id, "cancele a reserva do lote L1")
        resultado = await service.confirmar(tenant.id, pendente.confirmacao.confirmacao_id, aprovado=False)

    assert resultado.resposta == "Ok, mantive a reserva."
    await db_session.refresh(reserva)
    assert reserva.status == StatusReservaVenda.RESERVADO

    total_auditado = (
        await db_session.execute(
            select(AuditLog).where(
                AuditLog.entidade_id == reserva.id, AuditLog.acao == AcaoAuditoria.CANCELAMENTO_RESERVA
            )
        )
    ).scalars().all()
    assert total_auditado == []


@pytest.mark.asyncio
async def test_confirmar_com_tenant_diferente_do_pedido_original_falha(db_session: AsyncSession, monkeypatch):
    tenant, usuario, reserva = await _cenario_com_reserva(db_session, "confirmacao-tenant-errado")
    monkeypatch.setattr(ai_rag, "llm_provider", _mock_llm_propoe_cancelamento(reserva.id, "não deveria chegar aqui"))

    service = AgenteService(db_session)
    with contexto_auditoria(usuario_id=usuario.id, tenant_id=tenant.id):
        pendente = await service.perguntar(tenant.id, "cancele a reserva do lote L1")

    with pytest.raises(ConfirmacaoNaoEncontradaError):
        await service.confirmar(uuid4(), pendente.confirmacao.confirmacao_id, aprovado=True)


@pytest.mark.asyncio
async def test_confirmacao_id_inexistente_falha(db_session: AsyncSession):
    service = AgenteService(db_session)
    with pytest.raises(ConfirmacaoNaoEncontradaError):
        await service.confirmar(uuid4(), uuid4(), aprovado=True)
