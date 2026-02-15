from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.compliance import ComplianceFlag

class ComplianceFlagRepository:
    """
    Repository for ComplianceFlag entity.
    Strict persistence layer. No business logic.
    """

    async def create_flag(self, session: AsyncSession, user_id: UUID, flag_data: Dict[str, Any]) -> ComplianceFlag:
        """
        Create a new compliance flag in the database.
        flag_data should contain:
        - financial_year
        - flag_code
        - description
        - severity
        """
        flag = ComplianceFlag(
            user_id=user_id,
            **flag_data
        )
        session.add(flag)
        await session.flush()
        await session.refresh(flag)
        return flag

    async def get_by_user_id(self, session: AsyncSession, user_id: UUID) -> List[ComplianceFlag]:
        """
        Retrieve all compliance flags for a specific user.
        """
        stmt = select(ComplianceFlag).where(ComplianceFlag.user_id == user_id)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_user_id_and_year(self, session: AsyncSession, user_id: UUID, financial_year: str) -> List[ComplianceFlag]:
        """
        Retrieve compliance flags for a user filtered by financial year.
        """
        stmt = select(ComplianceFlag).where(
            ComplianceFlag.user_id == user_id,
            ComplianceFlag.financial_year == financial_year
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, session: AsyncSession, flag_id: UUID) -> Optional[ComplianceFlag]:
        """
        Retrieve a specific compliance flag by ID.
        """
        stmt = select(ComplianceFlag).where(ComplianceFlag.id == flag_id)
        result = await session.execute(stmt)
        return result.scalars().first()

    async def mark_resolved(self, session: AsyncSession, flag_id: UUID, notes: Optional[str] = None) -> Optional[ComplianceFlag]:
        """
        Mark a flag as resolved.
        Updates is_resolved, resolved_at, and optionally resolution_notes.
        """
        # Fetch first to ensure existence and return updated object
        stmt = select(ComplianceFlag).where(ComplianceFlag.id == flag_id)
        result = await session.execute(stmt)
        flag = result.scalars().first()

        if flag:
            flag.is_resolved = True
            flag.resolved_at = datetime.now(timezone.utc)
            if notes:
                flag.resolution_notes = notes
            
            await session.flush()
            await session.refresh(flag)
            
        return flag
