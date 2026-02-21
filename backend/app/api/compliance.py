from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.user import User
from app.schemas.compliance import (
    ComplianceEvaluationRequest,
    ComplianceFlagResponse,
    ComplianceResolutionRequest
)
from app.services.compliance_service import ComplianceEngineService
from app.core.dependencies import get_db

router = APIRouter()

# Helper for Role Enforcement
def check_compliance_access(user: User):
    """
    Enforce that only INDIVIDUAL and BUSINESS roles can access compliance features.
    """
    if user.primary_role not in ["INDIVIDUAL", "BUSINESS"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Only Individual and Business profiles can manage compliance."
        )

@router.post("/evaluate", status_code=status.HTTP_200_OK)
async def evaluate_compliance(
    request: ComplianceEvaluationRequest,
    current_user: User = Depends(deps.get_current_user),
    service: ComplianceEngineService = Depends(deps.get_compliance_service),
    session: AsyncSession = Depends(get_db)
):
    """
    Trigger compliance evaluation for a specific financial year.
    Idempotent operation.
    """
    check_compliance_access(current_user)
    
    await service.evaluate_user(
        session=session,
        user_id=current_user.id,
        financial_year=request.financial_year
    )
    return {"message": "Compliance evaluation completed successfully."}

@router.get("/", response_model=List[ComplianceFlagResponse])
async def get_compliance_flags(
    financial_year: Optional[str] = None,
    current_user: User = Depends(deps.get_current_user),
    service: ComplianceEngineService = Depends(deps.get_compliance_service),
    session: AsyncSession = Depends(get_db)
):
    """
    Retrieve compliance flags for the current user.
    Optionally filter by financial year.
    """
    check_compliance_access(current_user)
    return await service.get_user_flags(session, current_user.id, financial_year)

@router.post("/{flag_id}/resolve", response_model=ComplianceFlagResponse)
async def resolve_flag(
    flag_id: UUID,
    request: ComplianceResolutionRequest,
    current_user: User = Depends(deps.get_current_user),
    service: ComplianceEngineService = Depends(deps.get_compliance_service),
    session: AsyncSession = Depends(get_db)
):
    """
    Mark a compliance flag as resolved.
    Strictly enforces ownership.
    """
    check_compliance_access(current_user)
    
    return await service.resolve_flag(session, current_user.id, flag_id, request.resolution_notes)
