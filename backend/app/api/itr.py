from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.api import deps
from app.models.user import User
from app.schemas.itr import ITRDeterminationRequest, ITRDeterminationResponse
from app.services.itr_service import ITRDeterminationService
from app.core.dependencies import get_db

router = APIRouter()

YEAR_REGEX = r"^\d{4}-\d{2}$"

def check_itr_access(user: User):
    """
    Enforce that only INDIVIDUAL and BUSINESS roles can access ITR features.
    """
    if user.primary_role not in ["INDIVIDUAL", "BUSINESS"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Only Individual and Business profiles can manage ITR determination."
        )

@router.post("/determine", response_model=ITRDeterminationResponse)
async def determine_itr(
    request: ITRDeterminationRequest,
    current_user: User = Depends(deps.get_current_user),
    service: ITRDeterminationService = Depends(deps.get_itr_service),
    session: AsyncSession = Depends(get_db)
):
    """
    Trigger ITR determination for a specific financial year.
    Returns the determined ITR type.
    """
    check_itr_access(current_user)
    
    try:
        return await service.determine_itr(
            session=session,
            user_id=current_user.id,
            financial_year=request.financial_year
        )
    except ValueError as e:
        status_code = status.HTTP_400_BAD_REQUEST
        if "locked" in str(e).lower():
            status_code = status.HTTP_403_FORBIDDEN
        raise HTTPException(status_code=status_code, detail=str(e))

@router.get("/", response_model=ITRDeterminationResponse)
async def get_determination(
    financial_year: str = Query(..., pattern=YEAR_REGEX, description="Financial Year (YYYY-YY)"),
    current_user: User = Depends(deps.get_current_user),
    service: ITRDeterminationService = Depends(deps.get_itr_service),
    session: AsyncSession = Depends(get_db)
):
    """
    Retrieve existing ITR determination for the user.
    """
    check_itr_access(current_user)
    
    determination = await service.get_determination(session, current_user.id, financial_year)
    if not determination:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ITR Determination not found")
        
    return determination

@router.post("/{financial_year}/lock", response_model=ITRDeterminationResponse)
async def lock_determination(
    financial_year: str = Path(..., pattern=YEAR_REGEX, description="Financial Year (YYYY-YY)"),
    current_user: User = Depends(deps.get_current_user),
    service: ITRDeterminationService = Depends(deps.get_itr_service),
    session: AsyncSession = Depends(get_db)
):
    """
    Lock the ITR determination for a specific financial year.
    Once locked, it cannot be re-determined.
    """
    check_itr_access(current_user)
    
    try:
        return await service.lock_determination(session, current_user.id, financial_year)
    except ValueError as e:
        status_code = status.HTTP_400_BAD_REQUEST
        if "not found" in str(e).lower():
            status_code = status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=status_code, detail=str(e))
