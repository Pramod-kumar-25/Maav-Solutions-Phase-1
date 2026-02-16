from datetime import datetime, timezone
from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.consent import CAAssignment, ConsentAuditLog
from app.repositories.consent_repository import ConsentRepository, CAAssignmentRepository, ConsentAuditRepository
from app.repositories.auth_repository import AuthRepository
from app.repositories.auth_repository import AuthRepository
from app.repositories.filing_repository import FilingCaseRepository
from app.core.exceptions import NotFoundError, UnauthorizedError, ValidationError

from app.services.evidence_service import EvidenceService

class CAAssignmentService:
    """
    Manages CA Assignments.
    Enforces role validation, filing mode, and consent linkage.
    Transactions are managed by the caller.
    """
    def __init__(
        self,
        consent_repo: ConsentRepository,
        assignment_repo: CAAssignmentRepository,
        audit_repo: ConsentAuditRepository,
        auth_repo: AuthRepository,
        filing_repo: FilingCaseRepository,
        evidence_service: EvidenceService
    ):
        self.consent_repo = consent_repo
        self.assignment_repo = assignment_repo
        self.audit_repo = audit_repo
        self.auth_repo = auth_repo
        self.filing_repo = filing_repo
        self.evidence_service = evidence_service

    async def assign_ca(
        self,
        session: AsyncSession,
        filing_id: UUID,
        taxpayer_id: UUID,
        ca_user_id: UUID,
        consent_id: UUID
    ) -> CAAssignment:
        """
        Assigns a CA to a Filing Case.
        Validated Consent, Roles, and Filing Ownership.
        """
        # 1. Fetch & Validate Filing using Repository
        filing = await self.filing_repo.get_by_id(session, filing_id)
        
        if not filing:
            raise NotFoundError("Filing Case not found")
        
        if filing.user_id != taxpayer_id:
            raise UnauthorizedError("Unauthorized to assign CA for this filing")
            
        if filing.filing_mode != "CA":
            raise ValidationError("Filing mode must be 'CA' to assign a Chartered Accountant")

        if filing.current_state not in ["DRAFT", "READY_FOR_REVIEW"]:
                raise ValidationError("Cannot assign CA in current state")

        # 2. Validate CA User
        ca_user = await self.auth_repo.get_user_by_id(session, ca_user_id)
        if not ca_user:
            raise NotFoundError("CA User not found")
        
        if ca_user.primary_role != "CA":
            raise ValidationError("Assigned user is not a Chartered Accountant")

        # 3. Validate Consent
        consent = await self.consent_repo.get_by_id(session, consent_id)
        if not consent:
            raise NotFoundError("Consent not found")
        
        if consent.user_id != taxpayer_id:
            raise UnauthorizedError("Consent does not belong to taxpayer")
            
        if consent.status != "ACTIVE":
            raise ValidationError("Consent is not active")
            
        if consent.expiry_at <= datetime.now(timezone.utc):
            raise ValidationError("Consent has expired")

        # 4. Check Duplicate
        existing = await self.assignment_repo.get_by_filing_id(session, filing_id)
        if existing and existing.status == "ACTIVE":
            raise ValidationError("An active CA assignment already exists for this filing")

        # 5. Create Assignment
        assignment = CAAssignment(
            filing_id=filing_id,
            ca_user_id=ca_user_id,
            consent_id=consent_id,
            assigned_at=datetime.now(timezone.utc),
            status="ACTIVE"
        )
        
        created_assignment = await self.assignment_repo.create_assignment(session, assignment)
        
        # Evidence Capture (Atomic)
        await self.evidence_service.capture_evidence(
            session=session,
            payload=created_assignment,
            action_urn=f"urn:assignment:{created_assignment.id}:assign"
        )
        
        # Audit Log (on Consent)
        await self.audit_repo.create_log(session, ConsentAuditLog(
            consent_id=consent_id,
            action="ASSIGNED",
            actor_id=taxpayer_id,
            reason=f"Assigned to CA {ca_user_id} for Filing {filing_id}"
        ))
        
        return created_assignment

    async def validate_ca_access(
        self,
        session: AsyncSession,
        filing_id: UUID,
        ca_user_id: UUID
    ) -> CAAssignment:
        """
        Validates that a CA has legitimate access to a filing.
        Checks:
        - Active Assignment Exists
        - Assigned to THIS CA
        - Underyling Consent is ACTIVE and UNEXPIRED within validation window
        """
        # 1. Fetch Assignment
        assignment = await self.assignment_repo.get_by_filing_id(session, filing_id)
        if not assignment:
            raise UnauthorizedError("No assignment found for this filing")

        if assignment.ca_user_id != ca_user_id:
            raise UnauthorizedError("Not assigned to this filing")

        if assignment.status != "ACTIVE":
            raise UnauthorizedError("Assignment is inactive")

        # 2. Fetch & Validate Consent
        consent = await self.consent_repo.get_by_id(session, assignment.consent_id)
        if not consent:
            raise UnauthorizedError("Underlying consent missing")

        if consent.status != "ACTIVE":
            raise UnauthorizedError("Consent has been revoked or is inactive")

        if consent.expiry_at <= datetime.now(timezone.utc):
            raise UnauthorizedError("Consent has expired")

        return assignment
