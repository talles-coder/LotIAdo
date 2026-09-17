"""ReservaVenda domain model."""
from enum import Enum

from sqlalchemy import Column, ForeignKey, String, UUID
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship

from app.audit.domain.acoes import AcaoAuditoria
from app.audit.infrastructure.tracking import rastrear_auditoria
from app.common.models import BaseModel


class TipoReservaVenda(str, Enum):
    """Se o registro é, no momento, uma reserva em aberto ou já uma venda concretizada."""

    RESERVA = "reserva"
    VENDA = "venda"


class StatusReservaVenda(str, Enum):
    """Estados possíveis de uma reserva/venda."""

    RESERVADO = "reservado"
    VENDIDO = "vendido"
    CANCELADA = "cancelada"


def _acao_para_mudanca_de_status(_antes: str, depois: str) -> AcaoAuditoria | None:
    if depois == StatusReservaVenda.CANCELADA.value:
        return AcaoAuditoria.CANCELAMENTO_RESERVA
    if depois == StatusReservaVenda.VENDIDO.value:
        return AcaoAuditoria.VENDA
    return None


def _enum_values(enum_cls: type[Enum]) -> list[str]:
    return [membro.value for membro in enum_cls]


@rastrear_auditoria(
    entidade="reserva",
    acao_criacao=AcaoAuditoria.CRIACAO_RESERVA,
    campos_sensiveis={"status": _acao_para_mudanca_de_status},
)
class ReservaVenda(BaseModel):
    """Reserva de um lote por um cliente, que pode evoluir para venda ou ser cancelada.

    O mesmo registro é atualizado in-place ao converter para venda (não se cria
    uma linha nova) — `tipo` e `status` mudam juntos nesse momento.
    """

    __tablename__ = "reservas_vendas"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    lote_id = Column(UUID(as_uuid=True), ForeignKey("lotes.id"), nullable=False)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=False)
    corretor_id = Column(UUID(as_uuid=True), ForeignKey("corretores.id"), nullable=True)
    tipo = Column(
        SAEnum(
            TipoReservaVenda,
            name="tipo_reserva_venda",
            native_enum=False,
            length=20,
            values_callable=_enum_values,
        ),
        nullable=False,
        default=TipoReservaVenda.RESERVA,
    )
    status = Column(
        SAEnum(
            StatusReservaVenda,
            name="status_reserva_venda",
            native_enum=False,
            length=20,
            values_callable=_enum_values,
        ),
        nullable=False,
        default=StatusReservaVenda.RESERVADO,
    )

    tenant = relationship("Tenant")
    lote = relationship("Lote")
    cliente = relationship("Cliente")
    corretor = relationship("Corretor")
