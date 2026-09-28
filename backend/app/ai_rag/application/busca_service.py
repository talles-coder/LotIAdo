"""Caso de uso de busca semântica sobre `document_chunks` (FASE7-IMPL-03)."""
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

import app.ai_rag as ai_rag
from app.ai_rag.domain.exceptions import LoteamentoDaBuscaNaoEncontradoError, LoteDaBuscaNaoEncontradoError
from app.ai_rag.infrastructure.repository import buscar_chunks_similares
from app.loteamentos_lotes.infrastructure.repository import get_lote_by_id, get_loteamento_by_id
from app.observabilidade.domain.chamada_ia import OrigemChamadaIA
from app.observabilidade.infrastructure.context import contexto_origem_ia

TOP_K_PADRAO = 5


@dataclass
class ResultadoBusca:
    chunk_id: UUID
    documento_id: UUID
    documento_nome: str
    texto: str
    ordem: int
    score: float


class BuscaService:
    """Gera o embedding da pergunta e consulta os chunks mais similares do tenant."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def buscar(
        self,
        tenant_id: UUID,
        pergunta: str,
        loteamento_id: UUID | None = None,
        lote_id: UUID | None = None,
        top_k: int = TOP_K_PADRAO,
    ) -> list[ResultadoBusca]:
        if loteamento_id is not None and await get_loteamento_by_id(self.db, tenant_id, loteamento_id) is None:
            raise LoteamentoDaBuscaNaoEncontradoError()
        if lote_id is not None and await get_lote_by_id(self.db, tenant_id, lote_id) is None:
            raise LoteDaBuscaNaoEncontradoError()

        with contexto_origem_ia(OrigemChamadaIA.RAG):
            embedding = await ai_rag.llm_provider.embed(pergunta)
        chunks_com_score = await buscar_chunks_similares(
            self.db, tenant_id, embedding, top_k, loteamento_id=loteamento_id, lote_id=lote_id
        )

        return [
            ResultadoBusca(
                chunk_id=chunk.id,
                documento_id=chunk.documento_id,
                documento_nome=chunk.documento.nome,
                texto=chunk.texto,
                ordem=chunk.ordem,
                score=score,
            )
            for chunk, score in chunks_com_score
        ]
