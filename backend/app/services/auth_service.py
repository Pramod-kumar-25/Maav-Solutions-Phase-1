from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.auth_repository import AuthRepository
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.schemas.token import Token
from app.models.user import User, UserCredentials, AuthSession
from app.utils.security import hash_password, verify_password
from app.core.config import settings
from datetime import datetime, timedelta
from jose import jwt

# Constants for Token Generation
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class AuthService:
    def __init__(self, auth_repo: AuthRepository):
        self.auth_repo = auth_repo

    def create_access_token(self, data: dict, expires_delta: timedelta | None = None) -> str:
        """
        Generates a JWT token with the given data.
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    async def register_user(self, session: AsyncSession, user_create: UserCreate) -> User:
        """
        Orchestrates user registration within an atomic transaction.
        """
        # 1. Check existing (Read-only, before transaction to save resources)
        existing_user = await self.auth_repo.get_user_by_email(session, user_create.email)
        if existing_user:
            raise ValueError("Email already registered")

        # 2. Hash Password (CPU-bound, outside transaction)
        hashed_pwd = hash_password(user_create.password)

        # 3. Transactional Write
        try:
            async with session.begin():
                # Create User
                new_user = User(
                    email=user_create.email,
                    legal_name=user_create.legal_name,
                    mobile=user_create.mobile,
                    pan=user_create.pan,
                    primary_role=user_create.primary_role
                )
                saved_user = await self.auth_repo.create_user(session, new_user)

                # Create Credentials
                credentials = UserCredentials(
                    user_id=saved_user.id,
                    auth_provider="PASSWORD",
                    password_hash=hashed_pwd
                )
                await self.auth_repo.create_user_credentials(session, credentials)
                
                return saved_user
        except Exception as e:
            # SQLAlchemy async IO automatically rolls back on exception exit from 'async with session.begin()'
            # We re-raise to let the controller handle arguments/logging
            raise e

    async def login_user(self, session: AsyncSession, user_login: UserLogin) -> Token:
        """
        Orchestrates user login with transactional session creation.
        """
        # 1. Find User & Verify (Read-only)
        user = await self.auth_repo.get_user_by_email(session, user_login.email)
        if not user or user.account_status != 'ACTIVE':
             raise ValueError("Invalid credentials")

        credentials = await self.auth_repo.get_credentials_by_user_id(session, user.id)
        if not credentials or not verify_password(user_login.password, credentials.password_hash):
            raise ValueError("Invalid credentials")

        # 2. Create Session (Transactional Write)
        session_expiry = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        async with session.begin():
            auth_session = AuthSession(
                user_id=user.id,
                auth_method="PASSWORD",
                session_expiry=session_expiry
            )
            await self.auth_repo.create_auth_session(session, auth_session)

        # 3. Generate Token (Real JWT)
        access_token = self.create_access_token(
            data={
                "sub": str(user.id),
                "primary_role": user.primary_role
            },
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        return Token(
            access_token=access_token, 
            token_type="bearer"
        )
