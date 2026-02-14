from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import ValidationError
from uuid import UUID
from app.core.config import settings
from app.core.dependencies import get_db
from app.models.user import User
from app.repositories.auth_repository import AuthRepository
from app.services.auth_service import AuthService

# Constants
ALGORITHM = "HS256"

# OAuth2 Scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_auth_repository() -> AuthRepository:
    """
    Dependency to provide AuthRepository instance.
    """
    return AuthRepository()

def get_auth_service(repo: AuthRepository = Depends(get_auth_repository)) -> AuthService:
    """
    Dependency to provide AuthService instance with injected Repository.
    """
    return AuthService(repo)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db),
    repo: AuthRepository = Depends(get_auth_repository)
) -> User:
    """
    Validates the JWT token and returns the current user.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = UUID(user_id_str)
    except (JWTError, ValidationError, ValueError):
        # ValueError handles invalid UUID string
        raise credentials_exception
        
    user = await repo.get_user_by_id(session, user_id=user_id)
    
    if user is None:
        raise credentials_exception
        
    if user.account_status != 'ACTIVE':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
        
    return user

# RBAC Foundation
from enum import Enum

class UserRole(str, Enum):
    INDIVIDUAL = "INDIVIDUAL"
    BUSINESS = "BUSINESS"
    CA = "CA"
    ADMIN = "ADMIN"

class RoleChecker:
    """
    Dependency factory for Role-Based Access Control.
    """
    def __init__(self, required_role: UserRole):
        self.required_role = required_role

    def __call__(self, user: User = Depends(get_current_user)) -> User:
        """
        Enforces that the user has the required role.
        """
        if user.primary_role != self.required_role.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return user

def require_role(role: UserRole) -> RoleChecker:
    """
    Helper to create the dependency.
    Usage: Depends(require_role(UserRole.ADMIN))
    """
    return RoleChecker(role)
