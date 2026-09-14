"""Ações sensíveis auditáveis, compartilhadas entre módulos.

Padronizar os nomes aqui evita que cada módulo invente sua própria string
para a mesma ação ao declarar `campos_sensiveis` em
`app.audit.infrastructure.tracking.rastrear_auditoria`.
"""
from enum import StrEnum


class AcaoAuditoria(StrEnum):
    """Ações sensíveis definidas em FASE1-IMPL-04 que devem gerar auditoria."""

    TRANSICAO_STATUS = "transicao_status"
    CRIACAO_RESERVA = "criacao_reserva"
    CANCELAMENTO_RESERVA = "cancelamento_reserva"
    VENDA = "venda"
    ALTERACAO_PRECO = "alteracao_preco"
    ALTERACAO_RESPONSAVEL = "alteracao_responsavel"
