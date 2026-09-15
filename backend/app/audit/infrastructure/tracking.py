"""Rastreamento automático de auditoria via eventos do SQLAlchemy.

Em vez de cada módulo lembrar de chamar uma função de auditoria manualmente
ao final de cada ação sensível, um model marcado com
`@rastrear_auditoria(...)` tem suas mudanças auditadas automaticamente por
um listener de `before_flush` registrado uma única vez neste módulo.
Este módulo é importado (por efeito colateral) em `app.database`, então o
listener fica ativo em toda a aplicação, scripts e testes sem nenhuma
configuração extra por request/rota/service — é só declarar quais campos
do model são sensíveis, uma vez, junto da definição do model.

Isso cobre as ações sensíveis descritas em FASE1-IMPL-04: transição de
status, alteração de preço, alteração de responsável (mudança de um campo
já rastreado) e criação de reserva (insert de um model com `acao_criacao`).
Se mais de um campo sensível mudar no mesmo flush e resolver para a mesma
ação, viram uma única entrada com um payload contendo todos os campos —
nunca uma linha por campo alterado.

Não há um helper manual paralelo: não existe hoje, no projeto, uma ação
sensível que não seja expressável como "um ou mais campos de um model
mudaram" — se isso mudar (payload que não vem de uma coluna, ex.: motivo
digitado pelo usuário), aí sim vale adicionar uma via de escape.
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Callable
from uuid import UUID, uuid4

from sqlalchemy import event
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import get_history

from app.audit.domain.acoes import AcaoAuditoria
from app.audit.domain.models import AuditLog
from app.audit.infrastructure.context import contexto_auditoria_atual

ResolvedorAcao = AcaoAuditoria | Callable[[Any, Any], AcaoAuditoria | None]


@dataclass(frozen=True)
class _ModeloRastreado:
    entidade: str
    acao_criacao: AcaoAuditoria | None = None
    campos_sensiveis: dict[str, ResolvedorAcao] = field(default_factory=dict)


_modelos_rastreados: dict[type, _ModeloRastreado] = {}


def rastrear_auditoria(
    *,
    entidade: str,
    acao_criacao: AcaoAuditoria | None = None,
    campos_sensiveis: dict[str, ResolvedorAcao] | None = None,
) -> Callable[[type], type]:
    """Marca um model para ter mudanças auditadas automaticamente.

    `campos_sensiveis` mapeia nome do atributo -> ação, ou uma função
    `(valor_antes, valor_depois) -> AcaoAuditoria | None` para quando a ação
    depende do valor novo (ex.: status de reserva virando "cancelada" vs
    "venda"); devolver `None` na função significa "essa transição
    específica não é auditável".

    Exemplo:
        @rastrear_auditoria(
            entidade="lote",
            campos_sensiveis={
                "status": AcaoAuditoria.TRANSICAO_STATUS,
                "preco": AcaoAuditoria.ALTERACAO_PRECO,
                "corretor_id": AcaoAuditoria.ALTERACAO_RESPONSAVEL,
            },
        )
        class Lote(BaseModel):
            ...
    """

    def decorator(modelo: type) -> type:
        _modelos_rastreados[modelo] = _ModeloRastreado(
            entidade=entidade,
            acao_criacao=acao_criacao,
            campos_sensiveis=campos_sensiveis or {},
        )
        return modelo

    return decorator


def _serializar(valor: Any) -> Any:
    if isinstance(valor, UUID):
        return str(valor)
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    if isinstance(valor, Decimal):
        return str(valor)
    if isinstance(valor, Enum):
        return valor.value
    return valor


def _payload_criacao(obj: Any) -> dict[str, Any]:
    return {coluna.name: _serializar(getattr(obj, coluna.name)) for coluna in obj.__table__.columns}


_Mudanca = tuple[_ModeloRastreado, Any, AcaoAuditoria, dict[str, Any] | None, dict[str, Any] | None]


def _mudancas_para_auditar(session: Session) -> list[_Mudanca]:
    mudancas: list[_Mudanca] = []

    for obj in session.new:
        config = _modelos_rastreados.get(type(obj))
        if config is not None and config.acao_criacao is not None:
            # `id` tem default Python-side (uuid4) que só é aplicado ao gerar
            # o INSERT, depois de before_flush — precisamos dele agora para
            # popular `entidade_id`, então geramos aqui (mesmo valor que
            # seria gerado de qualquer forma) em vez de deixar pro flush.
            if obj.id is None:
                obj.id = uuid4()
            mudancas.append((config, obj, config.acao_criacao, None, _payload_criacao(obj)))

    for obj in session.dirty:
        config = _modelos_rastreados.get(type(obj))
        if config is None:
            continue

        # Se mais de um campo sensível mudar no mesmo flush (mesma ação de
        # negócio), viram UMA entrada só, com um payload contendo todos os
        # campos — não uma linha por campo alterado.
        payloads_por_acao: dict[AcaoAuditoria, tuple[dict[str, Any], dict[str, Any]]] = {}
        for campo, resolvedor in config.campos_sensiveis.items():
            historico = get_history(obj, campo)
            if not historico.added or not historico.deleted:
                continue
            valor_antes, valor_depois = historico.deleted[0], historico.added[0]
            if valor_antes == valor_depois:
                continue
            acao = resolvedor(valor_antes, valor_depois) if callable(resolvedor) else resolvedor
            if acao is None:
                continue
            payload_antes, payload_depois = payloads_por_acao.setdefault(acao, ({}, {}))
            payload_antes[campo] = _serializar(valor_antes)
            payload_depois[campo] = _serializar(valor_depois)

        for acao, (payload_antes, payload_depois) in payloads_por_acao.items():
            mudancas.append((config, obj, acao, payload_antes, payload_depois))

    return mudancas


@event.listens_for(Session, "before_flush")
def _auditar_antes_do_flush(session: Session, flush_context: Any, instances: Any) -> None:
    """Gera entradas de audit_log para as mudanças rastreadas deste flush."""
    if not _modelos_rastreados:
        return

    mudancas = _mudancas_para_auditar(session)
    if not mudancas:
        return

    usuario_id, tenant_id = contexto_auditoria_atual()
    if usuario_id is None or tenant_id is None:
        raise RuntimeError(
            "Alteração em entidade auditável sem contexto de auditoria definido. "
            "Numa request HTTP isso é populado automaticamente pelo "
            "AuditContextMiddleware; fora de uma request (scripts, jobs, testes), "
            "use app.audit.infrastructure.context.contexto_auditoria(...)."
        )

    for config, obj, acao, payload_antes, payload_depois in mudancas:
        session.add(
            AuditLog(
                tenant_id=tenant_id,
                usuario_id=usuario_id,
                acao=str(acao),
                entidade=config.entidade,
                entidade_id=obj.id,
                payload_antes=payload_antes,
                payload_depois=payload_depois,
            )
        )
