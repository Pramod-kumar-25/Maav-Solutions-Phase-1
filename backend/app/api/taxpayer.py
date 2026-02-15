from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from app.core.dependencies import get_db
from app.api.deps import get_current_user, require_role, UserRole, get_taxpayer_service
from app.models.user import User
from app.schemas.taxpayer import TaxpayerProfileCreate, TaxpayerProfileResponse
from app.services.taxpayer_service import TaxpayerProfileService

router = APIRouter(prefix="/taxpayer", tags=["Taxpayer Profile"])

@router.post(
    "/profile",
    response_model=TaxpayerProfileResponse,
    status_code=status.HTTP_201_CREATED,
    # Auth & Role check happens in the dependency injection of current_user
)
async def create_taxpayer_profile(
    profile_in: TaxpayerProfileCreate,
    current_user: User = Depends(require_role(UserRole.INDIVIDUAL)),
    session: AsyncSession = Depends(get_db),
    service: TaxpayerProfileService = Depends(get_taxpayer_service)
) -> Any:
    """
    Create a new Taxpayer Profile for the current user.
    - **Role Required**: INDIVIDUAL
    - **Calculates**: Residential Status automatically
    - **Constraint**: One profile per user
    """
    try:
        profile = await service.create_profile(session, current_user.id, profile_in)
        return profile
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get(
    "/profile",
    response_model=TaxpayerProfileResponse,
    # Auth & Role check happens in the dependency injection of current_user
)
async def get_my_taxpayer_profile(
    current_user: User = Depends(require_role(UserRole.INDIVIDUAL)),
    session: AsyncSession = Depends(get_db),
    service: TaxpayerProfileService = Depends(get_taxpayer_service)
) -> Any:
    """
    Retrieve the current user's Taxpayer Profile.
    """
    profile = await service.get_profile(session, current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Taxpayer profile not found"
        )
    return profile
