"""Invitation use cases: invite someone to a tenant, then accept the invite."""
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.identity.application.security import generate_invitation_token, hash_password
from app.identity.domain.exceptions import (
    InvitationExpiradoError,
    InvitationJaAceitoError,
    InvitationNaoEncontradoError,
    UsuarioJaAtivoNoTenantError,
)
from app.identity.domain.models import Invitation, User, UserTenantMembership
from app.identity.infrastructure.repository import (
    get_active_membership_for_email_and_tenant,
    get_invitation_by_token,
    get_membership_for_user_and_tenant,
    get_user_by_email,
)


class InvitationService:
    """Orchestrates inviting a user to a tenant and accepting that invite."""

    def __init__(self, db: AsyncSession, settings: Settings):
        self.db = db
        self.settings = settings

    async def convidar(
        self, tenant_id: UUID, invited_by_user_id: UUID, email: str, role: str
    ) -> Invitation:
        """Create a pending invitation for `email` to join the tenant with `role`."""
        if await get_active_membership_for_email_and_tenant(self.db, email, tenant_id) is not None:
            raise UsuarioJaAtivoNoTenantError()

        now = datetime.now(timezone.utc)
        invitation = Invitation(
            tenant_id=tenant_id,
            email=email,
            role=role,
            token=generate_invitation_token(),
            invited_by_user_id=invited_by_user_id,
            expires_at=now + timedelta(hours=self.settings.invitation_expire_hours),
        )
        self.db.add(invitation)
        await self.db.commit()
        return invitation

    async def aceitar(self, token: str, full_name: str, password: str) -> User:
        """Accept an invitation: create (or reuse) the user and activate their membership.

        Se já existe um `User` com esse e-mail (ex.: convidado para um
        segundo tenant), a membership é adicionada a ele e `full_name`/
        `password` do request são ignorados — aceitar um convite não é uma
        forma de redefinir a senha de outra conta.
        """
        invitation = await get_invitation_by_token(self.db, token)
        if invitation is None:
            raise InvitationNaoEncontradoError()
        if invitation.accepted_at is not None:
            raise InvitationJaAceitoError()
        if invitation.expires_at < datetime.now(timezone.utc):
            raise InvitationExpiradoError()

        user = await get_user_by_email(self.db, invitation.email)
        if user is None:
            user = User(
                email=invitation.email,
                hashed_password=hash_password(password),
                full_name=full_name,
            )
            self.db.add(user)
            await self.db.flush()

        membership = await get_membership_for_user_and_tenant(self.db, user.id, invitation.tenant_id)
        if membership is None:
            membership = UserTenantMembership(
                user_id=user.id,
                tenant_id=invitation.tenant_id,
                role=invitation.role,
                is_active=True,
            )
            self.db.add(membership)
        else:
            membership.role = invitation.role
            membership.is_active = True

        invitation.accepted_at = datetime.now(timezone.utc)
        await self.db.commit()
        return user
