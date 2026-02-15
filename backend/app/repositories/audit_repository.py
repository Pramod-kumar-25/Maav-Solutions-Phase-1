from uuid import UUID
from typing import Sequence, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.audit import AuditLog

class AuditLogRepository:
    """
    Audit Log Repository.
    Handles persistence for system audit logs.
    """

    async def create_log(self, session: AsyncSession, log: AuditLog) -> AuditLog:
        """
        Persist a new Audit Log entry.
        """
        session.add(log)
        await session.flush()
        await session.refresh(log)
        return log

    async def get_by_user(self, session: AsyncSession, actor_id: UUID) -> Sequence[AuditLog]:
        """
        Retrieve audit logs for a specific actor (user).
        """
        result = await session.execute(
            select(AuditLog)
            .where(AuditLog.actor_id == actor_id)
            .order_by(AuditLog.created_at.desc())
        )
        return result.scalars().all()

    # NOTE: get_by_entity is omitted because 'entity_type' and 'entity_id' 
    # columns do not exist in the current schema (as per strict revert instructions).
