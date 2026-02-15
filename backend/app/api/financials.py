from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from uuid import UUID

from app.api import deps
from app.models.user import User
from app.schemas.financials import FinancialEntryCreate, FinancialEntryResponse
from app.services.financial_service import FinancialEntryService

router = APIRouter()


# Role Enforcement
from app.api.deps import UserRole

def check_financial_access(user: User):
    """
    Enforce that only INDIVIDUAL and BUSINESS roles can access financial ledger.
    """
    if user.primary_role not in [UserRole.INDIVIDUAL.value, UserRole.BUSINESS.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Only Individual and Business profiles can manage financial entries."
        )

@router.post("/", response_model=FinancialEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_financial_entry(
    entry_in: FinancialEntryCreate,
    current_user: User = Depends(deps.get_current_user),
    service: FinancialEntryService = Depends(deps.get_financial_service),
    session = Depends(deps.get_db)
):
    """
    Create a new financial entry (Income or Expense).
    Allowed Roles: INDIVIDUAL, BUSINESS.
    """
    check_financial_access(current_user)
    try:
        # Pydantic model dump
        entry_data = entry_in.model_dump()
        
        return await service.create_entry(session, current_user.id, entry_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/", response_model=List[FinancialEntryResponse])
async def get_financial_entries(
    entry_type: Optional[str] = Query(None, pattern="^(INCOME|EXPENSE)$"),
    current_user: User = Depends(deps.get_current_user),
    service: FinancialEntryService = Depends(deps.get_financial_service),
    session = Depends(deps.get_db)
):
    """
    Retrieve financial entries.
    Allowed Roles: INDIVIDUAL, BUSINESS.
    """
    check_financial_access(current_user)
    try:
        if entry_type:
            return await service.get_user_entries_by_type(session, current_user.id, entry_type)
        else:
            return await service.get_user_entries(session, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_financial_entry(
    entry_id: UUID,
    current_user: User = Depends(deps.get_current_user),
    service: FinancialEntryService = Depends(deps.get_financial_service),
    session = Depends(deps.get_db)
):
    """
    Delete a financial entry by ID.
    Enforces ownership and role access.
    """
    check_financial_access(current_user)
    
    try:
        success = await service.delete_entry(session, current_user.id, entry_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    except ValueError as e:
        # Catch ownership violation
        if "Unauthorized" in str(e):
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
