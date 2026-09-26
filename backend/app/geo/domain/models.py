"""Modelos de domínio do módulo geo: feições de referência de um loteamento."""
from enum import Enum

from geoalchemy2 import Geometry
from sqlalchemy import Column, DateTime, ForeignKey, String, UUID
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship

from app.common.models import BaseModel


class TipoFeicao(str, Enum):
    """Tipo da feição de referência — base para consultas como "esquina" e "área verde"."""

    RUA = "rua"
    AREA_VERDE = "area_verde"
    OUTRO = "outro"


class FeicaoReferencia(BaseModel):
    """Geometria de referência (rua, área verde...) pertencente a um loteamento."""

    __tablename__ = "feicoes_referencia"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    loteamento_id = Column(UUID(as_uuid=True), ForeignKey("loteamentos.id"), nullable=False)
    tipo = Column(
        SAEnum(
            TipoFeicao,
            name="tipo_feicao",
            native_enum=False,
            length=20,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
    )
    nome = Column(String(255), nullable=True)
    # GEOMETRY genérico: rua costuma ser LineString, área verde Polygon.
    geometria = Column(Geometry("GEOMETRY", srid=4326), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    tenant = relationship("Tenant")
    loteamento = relationship("Loteamento")
