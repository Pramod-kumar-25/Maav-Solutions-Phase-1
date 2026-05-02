from typing import Optional, Any, Dict, Union
from uuid import UUID
from ipaddress import IPv4Address, IPv6Address
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditLog
from app.repositories.audit_repository import AuditLogRepository

class AuditService:
    """
    Audit Service.
    Wraps repository to provide a clean logging interface.
    """

    def __init__(self, audit_repo: AuditLogRepository):
        self.audit_repo = audit_repo

    async def log_action(
        self,
        session: AsyncSession,
        actor_id: Optional[UUID],
        actor_role: Optional[str],
        action: str,
        before_value: Optional[Dict[str, Any]] = None,
        after_value: Optional[Dict[str, Any]] = None,
        ip_address: Optional[Union[str, IPv4Address, IPv6Address]] = None,
        device_id: Optional[str] = None
    ) -> AuditLog:
        """
        Log an action in the system.
        """
        # Ensure IP is string if provided, although SQLAlchemy INET/String handles it.
        # String conversion is safer for INET fields if passing ipaddress objects.
        ip_str = str(ip_address) if ip_address else None

        log_entry = AuditLog(
            actor_id=actor_id,
            actor_role=actor_role,
            action=action,
            before_value=before_value,
            after_value=after_value,
            ip_address=ip_str,
            device_id=device_id,
            created_at=datetime.now(timezone.utc)
        )

        return await self.audit_repo.create_log(session, log_entry)

    async def get_user_logs(self, session: AsyncSession, user_id: UUID):
         """
         Retrieve logs for a user.
         """
         return await self.audit_repo.get_by_user(session, user_id)
