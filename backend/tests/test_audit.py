"""Tests for the audit module (trilha de auditoria imutável)."""
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.application.audit_service import registrar_auditoria
from app.audit.domain.acoes import AcaoAuditoria
from app.audit.domain.models import AuditLog
from app.identity.application.security import hash_password
from app.identity.domain.models import User
from app.tenancy.domain.models import Tenant


async def _criar_tenant_e_usuario(db: AsyncSession, slug: str) -> tuple[Tenant, User]:
    """Cria um tenant e um usuário mínimos para associar a uma entrada de auditoria."""
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
async def test_transicao_status_gera_uma_entrada_de_auditoria(db_session: AsyncSession):
    """Uma transição de status gera exatamente uma entrada de auditoria, com o payload correto."""
    tenant, user = await _criar_tenant_e_usuario(db_session, "tenant-audit-status")
    lote_id = uuid4()

    await registrar_auditoria(
        db_session,
        tenant_id=tenant.id,
        usuario_id=user.id,
        acao=AcaoAuditoria.TRANSICAO_STATUS,
        entidade="lote",
        entidade_id=lote_id,
        payload_antes={"status": "disponivel"},
        payload_depois={"status": "reservado"},
    )

    result = await db_session.execute(select(AuditLog).where(AuditLog.entidade_id == lote_id))
    entradas = result.scalars().all()

    assert len(entradas) == 1
    entrada = entradas[0]
    assert entrada.tenant_id == tenant.id
    assert entrada.usuario_id == user.id
    assert entrada.acao == AcaoAuditoria.TRANSICAO_STATUS
    assert entrada.entidade == "lote"
    assert entrada.payload_antes == {"status": "disponivel"}
    assert entrada.payload_depois == {"status": "reservado"}
    assert entrada.timestamp is not None


@pytest.mark.asyncio
async def test_criacao_reserva_gera_uma_entrada_de_auditoria(db_session: AsyncSession):
    """Uma criação de reserva gera exatamente uma entrada de auditoria, com o payload correto."""
    tenant, user = await _criar_tenant_e_usuario(db_session, "tenant-audit-reserva")
    reserva_id = uuid4()
    cliente_id = str(uuid4())
    lote_id = str(uuid4())

    await registrar_auditoria(
        db_session,
        tenant_id=tenant.id,
        usuario_id=user.id,
        acao=AcaoAuditoria.CRIACAO_RESERVA,
        entidade="reserva",
        entidade_id=reserva_id,
        payload_antes=None,
        payload_depois={"cliente_id": cliente_id, "lote_id": lote_id, "status": "reservado"},
    )

    result = await db_session.execute(select(AuditLog).where(AuditLog.entidade_id == reserva_id))
    entradas = result.scalars().all()

    assert len(entradas) == 1
    entrada = entradas[0]
    assert entrada.acao == AcaoAuditoria.CRIACAO_RESERVA
    assert entrada.entidade == "reserva"
    assert entrada.payload_antes is None
    assert entrada.payload_depois == {"cliente_id": cliente_id, "lote_id": lote_id, "status": "reservado"}


@pytest.mark.asyncio
async def test_multiplas_acoes_geram_entradas_independentes(db_session: AsyncSession):
    """Cada chamada a registrar_auditoria soma uma nova entrada, nunca substitui uma anterior."""
    tenant, user = await _criar_tenant_e_usuario(db_session, "tenant-audit-multiplas")
    reserva_id = uuid4()

    await registrar_auditoria(
        db_session,
        tenant_id=tenant.id,
        usuario_id=user.id,
        acao=AcaoAuditoria.CRIACAO_RESERVA,
        entidade="reserva",
        entidade_id=reserva_id,
        payload_depois={"status": "reservado"},
    )
    await registrar_auditoria(
        db_session,
        tenant_id=tenant.id,
        usuario_id=user.id,
        acao=AcaoAuditoria.CANCELAMENTO_RESERVA,
        entidade="reserva",
        entidade_id=reserva_id,
        payload_antes={"status": "reservado"},
        payload_depois={"status": "disponivel"},
    )

    result = await db_session.execute(
        select(AuditLog).where(AuditLog.entidade_id == reserva_id).order_by(AuditLog.timestamp)
    )
    entradas = result.scalars().all()

    assert len(entradas) == 2
    assert entradas[0].acao == AcaoAuditoria.CRIACAO_RESERVA
    assert entradas[1].acao == AcaoAuditoria.CANCELAMENTO_RESERVA


def test_audit_repository_so_expoe_create():
    """audit_log é append-only: o repositório não expõe update/delete/save."""
    import app.audit.infrastructure.repository as audit_repository

    funcoes_publicas = {name for name in dir(audit_repository) if not name.startswith("_")}
    proibidas = {"update", "delete", "remove", "save"}

    assert "create" in funcoes_publicas
    assert not (funcoes_publicas & proibidas)
