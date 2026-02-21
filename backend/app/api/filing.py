from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.api import deps
from app.models.user import User
from app.schemas.filing import FilingCaseCreate, FilingCaseResponse, FilingCaseTransition, YEAR_REGEX
from app.services.filing_service import FilingCaseService
from app.core.dependencies import get_db

router = APIRouter()

def check_access(user: User):
    """
    Enforce that only INDIVIDUAL and BUSINESS roles can access Filing features.
    """
    if user.primary_role not in ["INDIVIDUAL", "BUSINESS"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Role not authorized."
        )

@router.post("/", response_model=FilingCaseResponse, status_code=status.HTTP_201_CREATED)
async def create_filing_case(
    request: FilingCaseCreate,
    current_user: User = Depends(deps.get_current_user),
    service: FilingCaseService = Depends(deps.get_filing_service),
    session: AsyncSession = Depends(get_db)
):
    """
    Initialize a new Filing Case.
    User must have a LOCKED ITR Determination first.
    """
    check_access(current_user)
    
    return await service.create_case(
        session=session,
        user_id=current_user.id,
        financial_year=request.financial_year,
        itr_determination_id=request.itr_determination_id
    )

@router.get("/", response_model=FilingCaseResponse)
async def get_filing_case(
    financial_year: str = Query(..., pattern=YEAR_REGEX, description="Financial Year (YYYY-YY)"),
    current_user: User = Depends(deps.get_current_user),
    service: FilingCaseService = Depends(deps.get_filing_service),
    session: AsyncSession = Depends(get_db)
):
    """
    Retrieve existing Filing Case.
    """
    check_access(current_user)
    
    case = await service.get_case(session, current_user.id, financial_year)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Filing Case not found")
        
    return case

@router.post("/{financial_year}/transition", response_model=FilingCaseResponse)
async def transition_state(
    transition: FilingCaseTransition,
    financial_year: str = Path(..., pattern=YEAR_REGEX),
    current_user: User = Depends(deps.get_current_user),
    service: FilingCaseService = Depends(deps.get_filing_service),
    session: AsyncSession = Depends(get_db)
):
    """
    Transition Filing Case to next state.
    Strict State Machine enforcement.
    """
    check_access(current_user)
    
    return await service.transition_state(
        session=session,
        user_id=current_user.id,
        financial_year=financial_year,
        next_state=transition.next_state
    )
