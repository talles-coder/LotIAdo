"""Middleware que atribui um `request_id` a cada request, para correlação nos logs de IA (FASE10-IMPL-01).

Roda para toda request, registrado uma única vez em `app.main` — nenhuma rota
precisa declarar nada para que as chamadas de IA feitas durante essa request
(possivelmente mais de uma: RAG busca+gera, agente decide em loop) fiquem
correlacionadas pelo mesmo `request_id` no log estruturado (`app.observabilidade
.infrastructure.llm_logging`).
"""
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.observabilidade.infrastructure.context import contexto_request_id


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Gera (ou propaga, se o client já mandou `X-Request-Id`) um id único por request."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-Id") or str(uuid4())
        with contexto_request_id(request_id):
            response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        return response
