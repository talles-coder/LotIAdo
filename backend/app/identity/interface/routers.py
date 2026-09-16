"""Identity module HTTP routes."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.database import get_db
from app.identity.application.auth_service import AuthService
from app.identity.application.invitation_service import InvitationService
from app.identity.application.membership_service import MembershipService
from app.identity.domain.exceptions import (
    InvalidCredentialsError,
    InvitationExpiradoError,
    InvitationJaAceitoError,
    InvitationNaoEncontradoError,
    MembershipNaoEncontradaError,
    UsuarioJaAtivoNoTenantError,
)
from app.identity.domain.models import User
from app.identity.interface.dependencies import (
    get_current_tenant_id,
    get_current_user,
    get_settings,
    require_permission,
)
from app.identity.interface.schemas import (
    InvitationAcceptRequest,
    InvitationAcceptResponse,
    InvitationCreateRequest,
    InvitationResponse,
    LoginRequest,
    LoginResponse,
    UserMeResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> LoginResponse:
    """Authenticate with email/password and receive a JWT access token."""
    service = AuthService(db, settings)
    try:
        token = await service.login(request.email, request.password)
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    return LoginResponse(access_token=token)


@router.get("/me", response_model=UserMeResponse)
async def me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> UserMeResponse:
    """Return the authenticated user and their current tenant."""
    service = AuthService(db, settings)
    user, tenant_id = await service.get_current_user_with_tenant(current_user)
    return UserMeResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        tenant_id=tenant_id,
    )


@router.post("/invitations", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
async def convidar_usuario(
    request: InvitationCreateRequest,
    tenant_id: UUID = Depends(get_current_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_permission("usuarios:gerenciar")),
) -> InvitationResponse:
    """Convida um e-mail para se juntar ao tenant autenticado com o papel informado.

    Não há envio de e-mail (fora do escopo do MVP): o token do convite volta
    na própria resposta.
    """
    service = InvitationService(db, settings)
    try:
        invitation = await service.convidar(tenant_id, current_user.id, request.email, request.role)
    except UsuarioJaAtivoNoTenantError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este e-mail já é um membro ativo do tenant",
        )
    return InvitationResponse.model_validate(invitation)


@router.post("/invitations/{token}/accept", response_model=InvitationAcceptResponse)
async def aceitar_convite(
    token: str,
    request: InvitationAcceptRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> InvitationAcceptResponse:
    """Aceita um convite pendente, criando/ativando o usuário e sua membership no tenant.

    Rota pública: quem aceita ainda não tem sessão autenticada.
    """
    service = InvitationService(db, settings)
    try:
        user = await service.aceitar(token, request.full_name, request.password)
    except InvitationNaoEncontradoError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Convite não encontrado")
    except InvitationJaAceitoError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Convite já foi aceito")
    except InvitationExpiradoError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Convite expirado")
    return InvitationAcceptResponse.model_validate(user)


@router.post("/memberships/{membership_id}/deactivate", status_code=status.HTTP_204_NO_CONTENT)
async def desativar_membership(
    membership_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("usuarios:gerenciar")),
) -> None:
    """Desativa a membership de um usuário no tenant autenticado (sem apagar histórico)."""
    service = MembershipService(db)
    try:
        await service.desativar(tenant_id, membership_id)
    except MembershipNaoEncontradaError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership não encontrada")
