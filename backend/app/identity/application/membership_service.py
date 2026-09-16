"""Membership use cases: deactivating a user's access to a tenant."""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.identity.domain.exceptions import MembershipNaoEncontradaError
from app.identity.domain.models import UserTenantMembership
from app.identity.infrastructure.repository import get_membership_by_id_and_tenant


class MembershipService:
    """Orchestrates deactivating a membership, scoped to a tenant."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def desativar(self, tenant_id: UUID, membership_id: UUID) -> UserTenantMembership:
        """Deactivate a membership: the user keeps their history but can no longer act in the tenant.

        Não deleta a linha — histórico (auditoria, corretor em reservas
        passadas etc.) continua íntegro. Um token JWT já emitido para essa
        membership para de funcionar no próximo request (ver
        `get_current_tenant_id`, que resolve a membership no banco a cada
        chamada, não confia só no claim do JWT).
        """
        membership = await get_membership_by_id_and_tenant(self.db, membership_id, tenant_id)
        if membership is None:
            raise MembershipNaoEncontradaError()

        membership.is_active = False
        await self.db.commit()
        return membership
