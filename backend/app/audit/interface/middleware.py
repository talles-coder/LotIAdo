"""Middleware que popula o contexto de auditoria a partir do JWT da request.

Roda para toda request automaticamente — é registrado uma única vez em
`app.main`, nenhuma rota precisa declarar nada para que as mudanças feitas
durante essa request fiquem auditadas quando tocarem uma entidade rastreada
(ver `app.audit.infrastructure.tracking.rastrear_auditoria`).

Não faz autenticação: só popula o contexto quando o token é válido. A
autenticação/autorização de cada rota continua sendo responsabilidade das
dependencies existentes (`get_current_user`, `get_current_tenant_id`).
"""
from uuid import UUID

import jwt
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.audit.infrastructure.context import contexto_auditoria
from app.config import Settings
from app.identity.application.security import decode_access_token


class AuditContextMiddleware(BaseHTTPMiddleware):
    """Decodifica o bearer token (se houver) e expõe usuário/tenant atuais."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        usuario_id, tenant_id = self._identidade_da_request(request)
        if usuario_id is None or tenant_id is None:
            return await call_next(request)

        with contexto_auditoria(usuario_id=usuario_id, tenant_id=tenant_id):
            return await call_next(request)

    @staticmethod
    def _identidade_da_request(request: Request) -> tuple[UUID | None, UUID | None]:
        authorization = request.headers.get("Authorization", "")
        if not authorization.startswith("Bearer "):
            return None, None

        token = authorization.removeprefix("Bearer ").strip()
        try:
            payload = decode_access_token(token, Settings())
        except jwt.PyJWTError:
            return None, None

        try:
            usuario_id = UUID(payload.get("sub", ""))
            tenant_id = UUID(payload.get("tenant_id", ""))
        except (ValueError, TypeError):
            return None, None

        return usuario_id, tenant_id
