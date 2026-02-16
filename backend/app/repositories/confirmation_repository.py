from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.filing import UserConfirmation

class ConfirmationRepository:
    """
    Repository for managing User Confirmations (Taxpayer Approvals).
    """

    async def create_confirmation(self, session: AsyncSession, confirmation: UserConfirmation) -> UserConfirmation:
        """
        Creates a new confirmation record.
        """
        session.add(confirmation)
        await session.flush()
        await session.refresh(confirmation)
        return confirmation

    async def get_latest_by_filing(self, session: AsyncSession, filing_id: UUID) -> Optional[UserConfirmation]:
        """
        Retrieves the latest confirmation for a specific filing.
        """
        result = await session.execute(
            select(UserConfirmation)
            .where(UserConfirmation.filing_id == filing_id)
            .order_by(desc(UserConfirmation.confirmed_at))
            .limit(1)
        )
        return result.scalar_one_or_none()
