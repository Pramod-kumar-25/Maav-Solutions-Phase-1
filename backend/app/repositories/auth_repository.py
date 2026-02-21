from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.models.user import User, UserCredentials, AuthSession

class AuthRepository:
    """
    Repository for Identity & Authentication entities.
    Handles persistence for User, UserCredentials, and AuthSession.
    """

    async def get_user_by_email(self, session: AsyncSession, email: str) -> User | None:
        """
        Retrieve a user by their email address.
        """
        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_user_by_id(self, session: AsyncSession, user_id: UUID) -> User | None:
        """
        Retrieve a user by their unique ID.
        """
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        return result.scalars().first()

    async def create_user(self, session: AsyncSession, user: User) -> User:
        """
        Persist a new User entity.
        """
        session.add(user)
        await session.flush()  # Generate ID and populate defaults
        await session.refresh(user)
        return user

    async def get_credentials_by_user_id(self, session: AsyncSession, user_id: UUID) -> UserCredentials | None:
        """
        Retrieve credentials for a specific user.
        """
        stmt = select(UserCredentials).where(UserCredentials.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_credentials_by_user_id_for_update(self, session: AsyncSession, user_id: UUID) -> UserCredentials | None:
        """
        Retrieve credentials for a specific user, locking the row to prevent lost update race conditions.
        """
        stmt = select(UserCredentials).where(UserCredentials.user_id == user_id).with_for_update()
        result = await session.execute(stmt)
        return result.scalars().first()

    async def create_user_credentials(self, session: AsyncSession, credentials: UserCredentials) -> UserCredentials:
        """
        Persist new UserCredentials.
        """
        session.add(credentials)
        await session.flush()
        await session.refresh(credentials)
        return credentials

    async def create_auth_session(self, session: AsyncSession, auth_session: AuthSession) -> AuthSession:
        """
        Persist a new AuthSession.
        """
        session.add(auth_session)
        await session.flush()
        await session.refresh(auth_session)
        return auth_session

    async def get_session_by_hash(self, session: AsyncSession, token_hash: str) -> AuthSession | None:
        """
        Retrieve an AuthSession by its refresh token hash.
        """
        stmt = select(AuthSession).where(AuthSession.refresh_token_hash == token_hash)
        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_session_by_id(self, session: AsyncSession, session_id: UUID) -> AuthSession | None:
        """
        Retrieve an AuthSession by its ID.
        """
        stmt = select(AuthSession).where(AuthSession.id == session_id)
        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_active_sessions_by_user_id(self, session: AsyncSession, user_id: UUID) -> list[AuthSession]:
        """
        Retrieve all active sessions for a user (useful for revocation).
        """
        stmt = select(AuthSession).where(
            AuthSession.user_id == user_id,
            AuthSession.status == 'ACTIVE'
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
