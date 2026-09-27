"""AI RAG module HTTP routes."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_rag.application.busca_service import BuscaService
from app.ai_rag.domain.exceptions import LoteamentoDaBuscaNaoEncontradoError, LoteDaBuscaNaoEncontradoError
from app.ai_rag.interface.schemas import BuscaSemanticaRequest, ChunkResultado
from app.identity.interface.dependencies import get_current_tenant_id
from app.tenancy.interface.dependencies import get_tenant_scoped_db

router = APIRouter(tags=["ai_rag"])


@router.post("/rag/buscar", response_model=list[ChunkResultado])
async def buscar(
    payload: BuscaSemanticaRequest,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_tenant_scoped_db),
) -> list[ChunkResultado]:
    """Busca semântica: retorna os chunks mais relevantes para `pergunta`, escopados ao tenant."""
    service = BuscaService(db)
    try:
        resultados = await service.buscar(
            tenant_id,
            payload.pergunta,
            loteamento_id=payload.loteamento_id,
            lote_id=payload.lote_id,
            top_k=payload.top_k,
        )
    except LoteamentoDaBuscaNaoEncontradoError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loteamento não encontrado")
    except LoteDaBuscaNaoEncontradoError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lote não encontrado")

    return [ChunkResultado.model_validate(resultado) for resultado in resultados]
