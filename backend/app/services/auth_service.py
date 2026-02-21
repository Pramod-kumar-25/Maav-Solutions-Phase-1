from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.auth_repository import AuthRepository
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.schemas.token import Token
from app.models.user import User, UserCredentials, AuthSession
from app.utils.security import hash_password, verify_password
from app.core.config import settings
from datetime import datetime, timedelta, timezone
from jose import jwt
from app.core.exceptions import NotFoundError, UnauthorizedError, ValidationError
import secrets
import hashlib
from uuid import uuid4, UUID

class AuthService:
    def __init__(self, auth_repo: AuthRepository):
        self.auth_repo = auth_repo

    def create_access_token(self, data: dict, expires_delta: timedelta | None = None) -> str:
        """
        Generates a JWT token with the given data.
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt

    async def register_user(self, session: AsyncSession, user_create: UserCreate) -> User:
        """
        Orchestrates user registration within an atomic transaction.
        """
        # 1. Check existing (Read-only, before transaction to save resources)
        existing_user = await self.auth_repo.get_user_by_email(session, user_create.email)
        if existing_user:
            raise ValidationError("Email already registered")

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
             raise UnauthorizedError("Invalid credentials")

        credentials = await self.auth_repo.get_credentials_by_user_id(session, user.id)
        if not credentials or not verify_password(user_login.password, credentials.password_hash):
            raise UnauthorizedError("Invalid credentials")

        # 2. Create Session (Transactional Write)
        session_expiry = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        raw_refresh_token = secrets.token_hex(64)
        refresh_token_hash = hashlib.sha256(raw_refresh_token.encode()).hexdigest()
        
        async with session.begin():
            auth_session = AuthSession(
                user_id=user.id,
                auth_method="PASSWORD",
                session_expiry=session_expiry,
                refresh_token_hash=refresh_token_hash,
                status="ACTIVE"
            )
            created_session = await self.auth_repo.create_auth_session(session, auth_session)

        full_refresh_token = f"{created_session.id}:{raw_refresh_token}"

        # 3. Generate Token (Real JWT)
        access_token = self.create_access_token(
            data={
                "sub": str(user.id),
                "primary_role": user.primary_role,
                "sid": str(created_session.id),
                "jti": str(uuid4())
            },
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        return Token(
            access_token=access_token, 
            token_type="bearer",
            refresh_token=full_refresh_token
        )

    async def refresh_access_token(self, session: AsyncSession, full_refresh_token: str) -> Token:
        """
        Rotates the refresh token and returns a new access/refresh token pair.
        Prevents replay attacks within a strict atomic transaction.
        """
        try:
            sid_str, raw_refresh_token = full_refresh_token.split(":", 1)
            sid = UUID(sid_str)
        except ValueError:
            raise UnauthorizedError("Invalid refresh token format")

        token_hash = hashlib.sha256(raw_refresh_token.encode()).hexdigest()
        
        async with session.begin():
            auth_session = await self.auth_repo.get_session_by_id(session, sid)
            
            if not auth_session:
                raise UnauthorizedError("Invalid refresh token")
                
            if auth_session.status != 'ACTIVE':
                raise UnauthorizedError("Session is revoked or expired")
                
            # Replay Detection
            if auth_session.refresh_token_hash != token_hash:
                auth_session.status = "REVOKED"
                raise UnauthorizedError("Refresh token reuse detected")
                
            if auth_session.session_expiry < datetime.now(timezone.utc):
                auth_session.status = "EXPIRED"
                raise UnauthorizedError("Refresh token expired")
                
            user = await self.auth_repo.get_user_by_id(session, auth_session.user_id)
            if not user or user.account_status != 'ACTIVE':
                raise UnauthorizedError("User inactive or not found")
                
            # 1. Rotate
            new_raw_refresh = secrets.token_hex(64)
            new_hash = hashlib.sha256(new_raw_refresh.encode()).hexdigest()
            session_expiry = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            
            auth_session.refresh_token_hash = new_hash
            auth_session.session_expiry = session_expiry
            
        # Outside transaction, generate JWT
        access_token = self.create_access_token(
            data={
                "sub": str(user.id),
                "primary_role": user.primary_role,
                "sid": str(auth_session.id),
                "jti": str(uuid4())
            },
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            refresh_token=f"{auth_session.id}:{new_raw_refresh}"
        )

    async def logout_user(self, session: AsyncSession, full_refresh_token: str):
        """
        Marks an active session as REVOKED based on the refresh token.
        Atomic transaction ensures consistent state.
        """
        try:
            sid_str, raw_refresh_token = full_refresh_token.split(":", 1)
            sid = UUID(sid_str)
        except ValueError:
            return # Fail silently on invalid format to prevent enumeration

        token_hash = hashlib.sha256(raw_refresh_token.encode()).hexdigest()
        
        async with session.begin():
            auth_session = await self.auth_repo.get_session_by_id(session, sid)
            
            if auth_session and auth_session.status == 'ACTIVE':
                if auth_session.refresh_token_hash == token_hash:
                    auth_session.status = "REVOKED"
