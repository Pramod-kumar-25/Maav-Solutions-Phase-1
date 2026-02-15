from uuid import UUID
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.itr import ITRDetermination

class ITRDeterminationRepository:
    """
    ITR Determination Repository.
    Handles persistence for ITR logic.
    Strictly no business logic.
    """

    async def get_by_id(self, session: AsyncSession, determination_id: UUID) -> Optional[ITRDetermination]:
        """
        Retrieve ITR determination by ID.
        """
        result = await session.execute(
            select(ITRDetermination).where(ITRDetermination.id == determination_id)
        )
        return result.scalars().first()

    async def get_by_user_and_year(self, session: AsyncSession, user_id: UUID, financial_year: str) -> Optional[ITRDetermination]:
        """
        Retrieve ITR determination for a specific user and financial year.
        """
        result = await session.execute(
            select(ITRDetermination).where(
                ITRDetermination.user_id == user_id,
                ITRDetermination.financial_year == financial_year
            )
        )
        return result.scalars().first()

    async def create_determination(self, session: AsyncSession, determination: ITRDetermination) -> ITRDetermination:
        """
        Persist a new ITR determination.
        """
        session.add(determination)
        await session.flush()
        await session.refresh(determination)
        return determination

    async def update_determination(self, session: AsyncSession, determination: ITRDetermination, updated_data: Dict[str, Any]) -> ITRDetermination:
        """
        Update an existing determination.
        """
        for field, value in updated_data.items():
            setattr(determination, field, value)
        
        await session.flush()
        await session.refresh(determination)
        return determination
