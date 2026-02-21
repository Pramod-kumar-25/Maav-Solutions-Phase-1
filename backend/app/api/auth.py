from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db
from app.schemas.user import UserCreate, UserLogin, UserResponse, PasswordChange
from app.schemas.token import Token
from app.services.auth_service import AuthService
from .deps import get_auth_service, require_active_session
from app.models.user import User
from app.core.rate_limit import check_rate_limit
from app.core.exceptions import UnauthorizedError, ValidationError
from pydantic import BaseModel
from uuid import UUID

router = APIRouter()

def get_client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"

async def rate_limit_register(request: Request):
    ip = get_client_ip(request)
    await check_rate_limit(f"register:ip:{ip}", 3, 3600)

async def rate_limit_login(request: Request, user_in: UserLogin):
    ip = get_client_ip(request)
    normalized_email = user_in.email.strip().lower()
    await check_rate_limit(f"login:ip:{ip}", 5, 60)
    await check_rate_limit(f"login:email:{normalized_email}", 5, 60)

class RefreshRequest(BaseModel):
    refresh_token: str

async def rate_limit_refresh(request: Request, req: RefreshRequest):
    ip = get_client_ip(request)
    await check_rate_limit(f"refresh:ip:{ip}", 10, 60)
    try:
        sid_str, _ = req.refresh_token.split(":", 1)
        await check_rate_limit(f"refresh:sid:{sid_str}", 10, 60)
    except ValueError:
        pass

async def rate_limit_password_change(current_user: User = Depends(require_active_session)):
    await check_rate_limit(f"password_change:user:{current_user.id}", 3, 3600)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(rate_limit_register)])
async def register(
    user_in: UserCreate,
    session: AsyncSession = Depends(get_db),
    service: AuthService = Depends(get_auth_service)
):
    """
    Register a new user.
    """
    return await service.register_user(session, user_in)


@router.post("/login", response_model=Token, dependencies=[Depends(rate_limit_login)])
async def login(
    user_in: UserLogin,
    session: AsyncSession = Depends(get_db),
    service: AuthService = Depends(get_auth_service)
):
    """
    Authenticate a user and return a JWT token.
    """
    return await service.login_user(session, user_in)


@router.post("/refresh", response_model=Token, dependencies=[Depends(rate_limit_refresh)])
async def refresh_token_endpoint(
    req: RefreshRequest,
    session: AsyncSession = Depends(get_db),
    service: AuthService = Depends(get_auth_service)
):
    """
    Refresh access token using a valid refresh token.
    """
    return await service.refresh_access_token(session, req.refresh_token)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout_endpoint(
    req: RefreshRequest,
    session: AsyncSession = Depends(get_db),
    service: AuthService = Depends(get_auth_service)
):
    """
    Invalidate the current auth session.
    """
    try:
        await service.logout_user(session, req.refresh_token)
        return {"message": "Successfully logged out"}
    except Exception:
        return {"message": "Successfully logged out"}


@router.post("/change-password", status_code=status.HTTP_200_OK, dependencies=[Depends(rate_limit_password_change)])
async def change_password(
    req: PasswordChange,
    session: AsyncSession = Depends(get_db),
    service: AuthService = Depends(get_auth_service),
    current_user: User = Depends(require_active_session)
):
    """
    Securely rotate password and revoke other sessions.
    """
    active_sid = UUID(current_user.session_id)
    await service.change_password(
        session=session,
        user_id=current_user.id,
        current_password=req.current_password,
        new_password=req.new_password,
        active_session_id=active_sid
    )
    return {"message": "Password updated successfully"}
