from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.models.business import BusinessProfile

class BusinessRepository:
    """
    Repository for Business Profile entities.
    Handles persistence for BusinessProfile.
    """

    async def get_by_user_id(self, session: AsyncSession, user_id: UUID) -> BusinessProfile | None:
        """
        Retrieve a business profile by the associated user's ID.
        """
        stmt = select(BusinessProfile).where(BusinessProfile.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalars().first()

    async def create_profile(self, session: AsyncSession, profile: BusinessProfile) -> BusinessProfile:
        """
        Persist a new BusinessProfile entity.
        Warning: Caller must ensure profile doesn't already exist (1:1 constraint).
        """
        session.add(profile)
        await session.flush()  # Generate ID and populate defaults
        await session.refresh(profile)
        return profile

    async def update_profile(self, session: AsyncSession, profile: BusinessProfile) -> BusinessProfile:
        """
        Persist changes to an existing BusinessProfile entity.
        The entity object must be attached to the session.
        """
        session.add(profile) # Ensure it's in the session (idempotent if already attached)
        await session.flush()
        await session.refresh(profile)
        return profile
