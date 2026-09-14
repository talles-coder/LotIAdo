"""Database access for the audit module.

Só existe `create`: audit_log é append-only, então nenhuma função de
update/delete é exposta aqui de propósito (ver FASE1-IMPL-04).
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.domain.models import AuditLog


async def create(db: AsyncSession, audit_log: AuditLog) -> AuditLog:
    """Persist a new (and immutable) audit log entry."""
    db.add(audit_log)
    await db.commit()
    await db.refresh(audit_log)
    return audit_log
