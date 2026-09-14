"""Tests for automatic audit tracking (`rastrear_auditoria` + before_flush listener).

Simula como `loteamentos_lotes` (transição de status) e `vendas_reservas`
(criação/cancelamento de reserva, venda) vão se beneficiar da auditoria
automática, usando models de teste — esses dois módulos ainda não existem
no repositório (FASE1-IMPL-01/03, responsabilidade do Dev 1).
"""
import pytest
from sqlalchemy import Column, ForeignKey, String, UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.audit.domain.acoes import AcaoAuditoria
from app.audit.domain.models import AuditLog
from app.audit.infrastructure.context import contexto_auditoria
from app.audit.infrastructure.tracking import rastrear_auditoria
from app.common.models import BaseModel
from app.identity.application.security import hash_password
from app.identity.domain.models import User
from app.tenancy.domain.models import Tenant


@rastrear_auditoria(
    entidade="lote",
    campos_sensiveis={"status": AcaoAuditoria.TRANSICAO_STATUS},
)
class _LoteDeTeste(BaseModel):
    """Model de teste equivalente a `Lote` (FASE1-IMPL-01, ainda não implementado)."""

    __tablename__ = "test_lotes_auditoria"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    status = Column(String(50), nullable=False)


def _acao_para_mudanca_de_status_da_reserva(_antes: str, depois: str) -> AcaoAuditoria | None:
    if depois == "cancelada":
        return AcaoAuditoria.CANCELAMENTO_RESERVA
    if depois == "vendido":
        return AcaoAuditoria.VENDA
    return None


@rastrear_auditoria(
    entidade="reserva",
    acao_criacao=AcaoAuditoria.CRIACAO_RESERVA,
    campos_sensiveis={"status": _acao_para_mudanca_de_status_da_reserva},
)
class _ReservaDeTeste(BaseModel):
    """Model de teste equivalente a `ReservaVenda` (FASE1-IMPL-03, ainda não implementado)."""

    __tablename__ = "test_reservas_auditoria"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    status = Column(String(50), nullable=False)


@rastrear_auditoria(
    entidade="lote",
    campos_sensiveis={
        "preco": AcaoAuditoria.ALTERACAO_PRECO,
        "preco_promocional": AcaoAuditoria.ALTERACAO_PRECO,
    },
)
class _LoteComDoisCamposDeTeste(BaseModel):
    """Model de teste com dois campos que resolvem para a mesma ação."""

    __tablename__ = "test_lotes_dois_campos_auditoria"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    preco = Column(String(50), nullable=False)
    preco_promocional = Column(String(50), nullable=False)


async def _criar_tenant_e_usuario(db: AsyncSession, slug: str) -> tuple[Tenant, User]:
    tenant = Tenant(name=slug, slug=slug)
    db.add(tenant)
    await db.flush()

    user = User(
        email=f"{slug}@test.com",
        hashed_password=hash_password("senha123"),
        full_name="Test User",
    )
    db.add(user)
    await db.commit()

    return tenant, user


@pytest.mark.asyncio
async def test_mudar_campo_rastreado_gera_uma_entrada_automaticamente(db_session: AsyncSession):
    """Mudar um campo rastreado (ex.: status do lote) audita sozinho, sem chamar nada explicitamente."""
    tenant, user = await _criar_tenant_e_usuario(db_session, "tenant-tracking-status")

    with contexto_auditoria(usuario_id=user.id, tenant_id=tenant.id):
        lote = _LoteDeTeste(tenant_id=tenant.id, status="disponivel")
        db_session.add(lote)
        await db_session.commit()

        lote.status = "reservado"
        await db_session.commit()

    result = await db_session.execute(select(AuditLog).where(AuditLog.entidade_id == lote.id))
    entradas = result.scalars().all()

    assert len(entradas) == 1
    entrada = entradas[0]
    assert entrada.acao == AcaoAuditoria.TRANSICAO_STATUS
    assert entrada.entidade == "lote"
    assert entrada.tenant_id == tenant.id
    assert entrada.usuario_id == user.id
    assert entrada.payload_antes == {"status": "disponivel"}
    assert entrada.payload_depois == {"status": "reservado"}


@pytest.mark.asyncio
async def test_criar_entidade_rastreada_gera_uma_entrada_automaticamente(db_session: AsyncSession):
    """Criar uma entidade com `acao_criacao` audita sozinha, sem chamar nada explicitamente."""
    tenant, user = await _criar_tenant_e_usuario(db_session, "tenant-tracking-criacao")

    with contexto_auditoria(usuario_id=user.id, tenant_id=tenant.id):
        reserva = _ReservaDeTeste(tenant_id=tenant.id, status="reservado")
        db_session.add(reserva)
        await db_session.commit()

    result = await db_session.execute(select(AuditLog).where(AuditLog.entidade_id == reserva.id))
    entradas = result.scalars().all()

    assert len(entradas) == 1
    entrada = entradas[0]
    assert entrada.acao == AcaoAuditoria.CRIACAO_RESERVA
    assert entrada.entidade == "reserva"
    assert entrada.payload_antes is None
    assert entrada.payload_depois["status"] == "reservado"
    assert entrada.payload_depois["id"] == str(reserva.id)


@pytest.mark.asyncio
async def test_acao_de_mudanca_de_campo_pode_depender_do_valor_novo(db_session: AsyncSession):
    """Duas mudanças de valor no mesmo campo podem virar ações diferentes (cancelamento vs venda)."""
    tenant, user = await _criar_tenant_e_usuario(db_session, "tenant-tracking-valor")

    with contexto_auditoria(usuario_id=user.id, tenant_id=tenant.id):
        reserva_cancelada = _ReservaDeTeste(tenant_id=tenant.id, status="reservado")
        reserva_vendida = _ReservaDeTeste(tenant_id=tenant.id, status="reservado")
        db_session.add_all([reserva_cancelada, reserva_vendida])
        await db_session.commit()

        reserva_cancelada.status = "cancelada"
        reserva_vendida.status = "vendido"
        await db_session.commit()

    result_cancelada = await db_session.execute(
        select(AuditLog).where(
            AuditLog.entidade_id == reserva_cancelada.id,
            AuditLog.acao == AcaoAuditoria.CANCELAMENTO_RESERVA,
        )
    )
    result_vendida = await db_session.execute(
        select(AuditLog).where(
            AuditLog.entidade_id == reserva_vendida.id,
            AuditLog.acao == AcaoAuditoria.VENDA,
        )
    )

    assert len(result_cancelada.scalars().all()) == 1
    assert len(result_vendida.scalars().all()) == 1


@pytest.mark.asyncio
async def test_mudar_campo_nao_rastreado_nao_gera_auditoria(db_session: AsyncSession):
    """Um campo fora de `campos_sensiveis` não é uma ação sensível — não deve gerar log."""
    tenant, user = await _criar_tenant_e_usuario(db_session, "tenant-tracking-irrelevante")

    with contexto_auditoria(usuario_id=user.id, tenant_id=tenant.id):
        reserva = _ReservaDeTeste(tenant_id=tenant.id, status="reservado")
        db_session.add(reserva)
        await db_session.commit()

        reserva.status = "reservado_atualizado_mas_sem_mapeamento"
        await db_session.commit()

    result = await db_session.execute(
        select(AuditLog).where(
            AuditLog.entidade_id == reserva.id,
            AuditLog.acao != AcaoAuditoria.CRIACAO_RESERVA,
        )
    )
    assert result.scalars().all() == []


@pytest.mark.asyncio
async def test_duas_mudancas_com_a_mesma_acao_no_mesmo_commit_viram_uma_entrada(db_session: AsyncSession):
    """Dois campos sensíveis mudando juntos (mesma ação) geram uma entrada com payload combinado, não duas linhas."""
    tenant, user = await _criar_tenant_e_usuario(db_session, "tenant-tracking-agrupado")

    with contexto_auditoria(usuario_id=user.id, tenant_id=tenant.id):
        lote = _LoteComDoisCamposDeTeste(tenant_id=tenant.id, preco="100", preco_promocional="90")
        db_session.add(lote)
        await db_session.commit()

        lote.preco = "120"
        lote.preco_promocional = "100"
        await db_session.commit()

    result = await db_session.execute(select(AuditLog).where(AuditLog.entidade_id == lote.id))
    entradas = result.scalars().all()

    assert len(entradas) == 1
    entrada = entradas[0]
    assert entrada.acao == AcaoAuditoria.ALTERACAO_PRECO
    assert entrada.payload_antes == {"preco": "100", "preco_promocional": "90"}
    assert entrada.payload_depois == {"preco": "120", "preco_promocional": "100"}


@pytest.mark.asyncio
async def test_mudanca_sem_contexto_de_auditoria_falha_alto_e_nao_silencioso(db_session: AsyncSession):
    """Alterar uma entidade rastreada sem contexto de auditoria falha (não perde o rastro em silêncio)."""
    tenant, _user = await _criar_tenant_e_usuario(db_session, "tenant-tracking-sem-contexto")

    lote = _LoteDeTeste(tenant_id=tenant.id, status="disponivel")
    db_session.add(lote)
    await db_session.commit()

    lote.status = "reservado"
    with pytest.raises(RuntimeError):
        await db_session.commit()
