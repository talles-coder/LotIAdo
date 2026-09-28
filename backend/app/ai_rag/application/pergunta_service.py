"""Caso de uso de geração de resposta com citação de fonte (FASE7-IMPL-04)."""
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

import app.ai_rag as ai_rag
from app.ai_rag.application.busca_service import TOP_K_PADRAO, BuscaService, ResultadoBusca
from app.observabilidade.domain.chamada_ia import OrigemChamadaIA
from app.observabilidade.infrastructure.context import contexto_origem_ia

SCORE_MINIMO_RELEVANTE = 0.5
RESPOSTA_SEM_CONTEXTO = "Não encontrei informação sobre isso nos documentos disponíveis."


@dataclass
class FonteCitada:
    documento_id: UUID
    documento_nome: str
    trecho: str


@dataclass
class RespostaGerada:
    resposta: str
    fontes: list[FonteCitada]


class PerguntaService:
    """Recupera os chunks relevantes, monta o prompt com grounding e gera a resposta final."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.busca_service = BuscaService(db)

    async def perguntar(
        self,
        tenant_id: UUID,
        pergunta: str,
        loteamento_id: UUID | None = None,
        lote_id: UUID | None = None,
        top_k: int = TOP_K_PADRAO,
    ) -> RespostaGerada:
        resultados = await self.busca_service.buscar(
            tenant_id, pergunta, loteamento_id=loteamento_id, lote_id=lote_id, top_k=top_k
        )
        relevantes = [resultado for resultado in resultados if resultado.score >= SCORE_MINIMO_RELEVANTE]

        if not relevantes:
            return RespostaGerada(resposta=RESPOSTA_SEM_CONTEXTO, fontes=[])

        prompt = self._montar_prompt(pergunta, relevantes)
        with contexto_origem_ia(OrigemChamadaIA.RAG):
            resposta = await ai_rag.llm_provider.generate(prompt)

        fontes = [
            FonteCitada(documento_id=resultado.documento_id, documento_nome=resultado.documento_nome, trecho=resultado.texto)
            for resultado in relevantes
        ]
        return RespostaGerada(resposta=resposta, fontes=fontes)

    def _montar_prompt(self, pergunta: str, resultados: list[ResultadoBusca]) -> str:
        contexto = "\n\n".join(f"[Fonte: {resultado.documento_nome}]\n{resultado.texto}" for resultado in resultados)
        return (
            "Responda à pergunta usando apenas as informações do contexto abaixo, em português. "
            "Se o contexto não tiver a resposta, diga que não encontrou a informação em vez de inventar.\n\n"
            f"Contexto:\n{contexto}\n\nPergunta: {pergunta}\n\nResposta:"
        )
