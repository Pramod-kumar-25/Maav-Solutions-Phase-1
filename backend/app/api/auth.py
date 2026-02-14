from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.schemas.token import Token
from app.services.auth_service import AuthService
from .deps import get_auth_service

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    session: AsyncSession = Depends(get_db),
    service: AuthService = Depends(get_auth_service)
):
    """
    Register a new user.
    Delegates strictly to AuthService.
    """
    # 1. API functions as a "Controller" - wiring only.
    try:
        # 2. Pass transaction-scoped session to service
        user = await service.register_user(session, user_in)
        return user
    except ValueError as e:
        # 3. Translate Service Exceptions to HTTP Exceptions
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=Token)
async def login(
    user_in: UserLogin,
    session: AsyncSession = Depends(get_db),
    service: AuthService = Depends(get_auth_service)
):
    """
    Authenticate a user and return a JWT token.
    Delegates strictly to AuthService.
    """
    try:
        # 1. Delegate Logic
        token = await service.login_user(session, user_in)
        return token
    except ValueError as e:
        # 2. Handle specific auth failure
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
