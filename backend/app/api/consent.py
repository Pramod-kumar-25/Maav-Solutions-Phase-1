from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.api import deps
from app.models.user import User
from app.schemas.consent import ConsentCreate, ConsentResponse, CAAssignmentCreate, CAAssignmentResponse
from app.services.consent_service import ConsentService
from app.services.ca_assignment_service import CAAssignmentService
from app.core.dependencies import get_db
from app.core.exceptions import NotFoundError, UnauthorizedError, ValidationError

router = APIRouter()

def check_taxpayer_access(user: User):
    """
    Enforce that only INDIVIDUAL and BUSINESS roles can manage Consents/Assignments.
    """
    if user.primary_role not in ["INDIVIDUAL", "BUSINESS"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Only Taxpayers can perform this action."
        )

@router.post("/", response_model=ConsentResponse, status_code=status.HTTP_201_CREATED)
async def grant_consent(
    request: ConsentCreate,
    current_user: User = Depends(deps.get_current_user),
    service: ConsentService = Depends(deps.get_consent_service),
    session: AsyncSession = Depends(get_db)
):
    """
    Grant a new Consent Artifact.
    """
    check_taxpayer_access(current_user)
    
    try:
        res = await service.grant_consent(
            session=session,
            user_id=current_user.id,
            purpose=request.purpose,
            scope=request.scope,
            expiry_at=request.expiry_at
        )
        await session.commit()
        return res
    except Exception:
        await session.rollback()
        raise

@router.post("/{consent_id}/revoke", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_consent(
    consent_id: UUID,
    reason: str = Body(..., embed=True),
    current_user: User = Depends(deps.get_current_user),
    service: ConsentService = Depends(deps.get_consent_service),
    session: AsyncSession = Depends(get_db)
):
    """
    Revoke an existing Consent.
    """
    check_taxpayer_access(current_user)
    
    try:
        await service.revoke_consent(
            session=session,
            consent_id=consent_id,
            user_id=current_user.id,
            reason=reason
        )
        await session.commit()
    except Exception:
        await session.rollback()
        raise

@router.post("/assignments", response_model=CAAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def assign_ca(
    request: CAAssignmentCreate,
    current_user: User = Depends(deps.get_current_user),
    service: CAAssignmentService = Depends(deps.get_ca_assignment_service),
    session: AsyncSession = Depends(get_db)
):
    """
    Assign a CA to a Filing Case.
    """
    check_taxpayer_access(current_user)
    
    try:
        res = await service.assign_ca(
            session=session,
            filing_id=request.filing_id,
            taxpayer_id=current_user.id,
            ca_user_id=request.ca_user_id,
            consent_id=request.consent_id
        )
        await session.commit()
        return res
    except Exception:
        await session.rollback()
        raise


@router.get("/", response_model=list[ConsentResponse], status_code=status.HTTP_200_OK)
async def list_consents(
    current_user: User = Depends(deps.get_current_user),
    service: ConsentService = Depends(deps.get_consent_service),
    session: AsyncSession = Depends(get_db)
):
    """
    Return all consent artifacts belonging to the authenticated taxpayer.
    """
    check_taxpayer_access(current_user)
    return await service.consent_repo.get_by_user(session, current_user.id)


@router.get("/{consent_id}", response_model=ConsentResponse, status_code=status.HTTP_200_OK)
async def get_consent(
    consent_id: UUID,
    current_user: User = Depends(deps.get_current_user),
    service: ConsentService = Depends(deps.get_consent_service),
    session: AsyncSession = Depends(get_db)
):
    """
    Return details for a single consent artifact.
    """
    check_taxpayer_access(current_user)
    consent = await service.consent_repo.get_by_id(session, consent_id)
    if not consent or consent.user_id != current_user.id:
        raise NotFoundError("Consent not found")
    return consent

