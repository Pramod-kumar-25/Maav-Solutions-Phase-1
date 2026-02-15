from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.models.taxpayer import TaxpayerProfile

class TaxpayerRepository:
    """
    Repository for Taxpayer Profile entities.
    Handles persistence for TaxpayerProfile.
    """

    async def get_by_user_id(self, session: AsyncSession, user_id: UUID) -> TaxpayerProfile | None:
        """
        Retrieve a taxpayer profile by the associated user's ID.
        """
        stmt = select(TaxpayerProfile).where(TaxpayerProfile.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalars().first()

    async def create_profile(self, session: AsyncSession, profile: TaxpayerProfile) -> TaxpayerProfile:
        """
        Persist a new TaxpayerProfile entity.
        Warning: Caller must ensure profile doesn't already exist (1:1 constraint).
        """
        session.add(profile)
        await session.flush()  # Generate ID and populate defaults
        await session.refresh(profile)
        return profile

    async def update_profile(self, session: AsyncSession, profile: TaxpayerProfile) -> TaxpayerProfile:
        """
        Persist changes to an existing TaxpayerProfile entity.
        The entity object must be attached to the session.
        """
        session.add(profile) # Ensure it's in the session (idempotent if already attached)
        await session.flush()
        await session.refresh(profile)
        return profile
