from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.auth_repository import AuthRepository
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.schemas.token import Token
from app.models.user import User, UserCredentials, AuthSession
from app.utils.security import hash_password, verify_password
from app.core.config import settings
from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext
from app.core.exceptions import NotFoundError, UnauthorizedError, ValidationError
import secrets
import hashlib
from uuid import uuid4, UUID

class AuthService:
    def __init__(self, auth_repo: AuthRepository):
        self.auth_repo = auth_repo
        # Initialize a dedicated context for dummy hashing to block timing attacks
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        # Pre-calculated dummy hash for a realistic delay
        self.dummy_hash = self.pwd_context.hash("dummy_password_for_timing_delay")

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
        Orchestrates user login with anti-enumeration, brute-force cooldown, and transactional session creation.
        """
        generic_error_msg = "Incorrect email or password. If you have reached maximum attempts, please try again in 15 minutes."
        cooldown_minutes = 15
        max_attempts = 5
        
        # 1. Fetch User (Read-only)
        user = await self.auth_repo.get_user_by_email(session, user_login.email)
        
        # Anti-Enumeration: If no user, perform dummy hash to simulate DB+Hash latency
        if not user or user.account_status != 'ACTIVE':
            self.pwd_context.verify(user_login.password, self.dummy_hash)
            raise UnauthorizedError(generic_error_msg)

        credentials = await self.auth_repo.get_credentials_by_user_id(session, user.id)
        if not credentials:
             self.pwd_context.verify(user_login.password, self.dummy_hash)
             raise UnauthorizedError(generic_error_msg)

        # 2. Check Cooldown Status
        now_utc = datetime.now(timezone.utc)
        if credentials.failed_attempts >= max_attempts and credentials.last_failed_login_at:
            time_since_last_fail = now_utc - credentials.last_failed_login_at
            if time_since_last_fail < timedelta(minutes=cooldown_minutes):
                # Cooldown active. Simulate hash delay to hide lockout status.
                self.pwd_context.verify(user_login.password, self.dummy_hash)
                raise UnauthorizedError(generic_error_msg)

        # 3. Verify Password
        is_valid = verify_password(user_login.password, credentials.password_hash)

        if not is_valid:
            # 4. Handle Failed Attempt (Atomic Write with Row Lock)
            async with session.begin():
                # Re-fetch credentials inside transaction with a row-level lock to prevent lost updates
                tx_credentials = await self.auth_repo.get_credentials_by_user_id_for_update(session, user.id)
                # Reset counter if previous cooldown expired
                if tx_credentials.failed_attempts >= max_attempts:
                    tx_credentials.failed_attempts = 1
                else:
                    tx_credentials.failed_attempts += 1
                
                tx_credentials.last_failed_login_at = now_utc
                # NOTE: Audit logging (LOGIN_FAILED / TEMPORARY_LOCKOUT_TRIGGERED) should hook here
            raise UnauthorizedError(generic_error_msg)

        # 5. Handle Successful Login & Session Creation (Atomic Write with Row Lock)
        session_expiry = now_utc + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        raw_refresh_token = secrets.token_hex(64)
        refresh_token_hash = hashlib.sha256(raw_refresh_token.encode()).hexdigest()
        
        async with session.begin():
            # Apply row-level lock for consistency
            tx_credentials = await self.auth_repo.get_credentials_by_user_id_for_update(session, user.id)
            tx_credentials.failed_attempts = 0
            tx_credentials.last_failed_login_at = None
            tx_credentials.last_login_at = now_utc

            auth_session = AuthSession(
                user_id=user.id,
                auth_method="PASSWORD",
                session_expiry=session_expiry,
                refresh_token_hash=refresh_token_hash,
                status="ACTIVE"
            )
            created_session = await self.auth_repo.create_auth_session(session, auth_session)

        full_refresh_token = f"{created_session.id}:{raw_refresh_token}"

        # 6. Generate Token (Real JWT)
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

    async def change_password(
        self, 
        session: AsyncSession, 
        user_id: UUID, 
        current_password: str, 
        new_password: str, 
        active_session_id: UUID
    ):
        """
        Securely changes the user's password and revokes all other active sessions.
        """
        if current_password == new_password:
            raise ValidationError("New password cannot be the same as the current password")
            
        credentials = await self.auth_repo.get_credentials_by_user_id(session, user_id)
        if not credentials or not verify_password(current_password, credentials.password_hash):
            raise UnauthorizedError("Incorrect current password")
            
        hashed_new_pwd = hash_password(new_password)
        
        async with session.begin():
            # 1. Update password
            tx_credentials = await self.auth_repo.get_credentials_by_user_id(session, user_id)
            tx_credentials.password_hash = hashed_new_pwd
            
            # 2. Invalidate all other active sessions
            active_sessions = await self.auth_repo.get_active_sessions_by_user_id(session, user_id)
            for s in active_sessions:
                if s.id != active_session_id:
                    s.status = 'REVOKED'
            # NOTE: Logging for SESSIONS_REVOKED / PASSWORD_CHANGED should hook here
