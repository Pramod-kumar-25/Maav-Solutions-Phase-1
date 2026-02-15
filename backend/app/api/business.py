from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from app.api.deps import get_business_service, require_role, UserRole
from app.schemas.business import BusinessProfileCreate, BusinessProfileResponse
from app.services.business_service import BusinessProfileService
from app.core.dependencies import get_db
from app.models.user import User

router = APIRouter()

@router.post("/profile", response_model=BusinessProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_business_profile(
    profile_in: BusinessProfileCreate,
    service: BusinessProfileService = Depends(get_business_service),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.BUSINESS))
) -> Any:
    """
    Create a new Business Profile.
    Restricted to users with 'BUSINESS' role.
    """
    try:
        return await service.create_profile(db, current_user.id, profile_in)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/profile", response_model=BusinessProfileResponse)
async def get_business_profile(
    service: BusinessProfileService = Depends(get_business_service),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.BUSINESS))
) -> Any:
    """
    Retrieve the Business Profile for the current user.
    """
    profile = await service.get_profile(db, current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found"
        )
    return profile
