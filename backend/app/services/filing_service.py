from datetime import datetime, timezone
from typing import Optional, Dict, Set
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.filing import FilingCase
from app.repositories.filing_repository import FilingCaseRepository
from app.repositories.itr_repository import ITRDeterminationRepository
from app.services.audit_service import AuditService
from app.services.evidence_service import EvidenceService

from app.core.exceptions import NotFoundError, UnauthorizedError, ValidationError
from app.repositories.confirmation_repository import ConfirmationRepository
from app.models.filing import UserConfirmation

class FilingCaseService:
    """
    Filing Case Workflow Engine.
    Enforces the strict state machine for Tax Return Filing.
    """

    # State Constants
    STATE_DRAFT = "DRAFT"
    STATE_REVIEW = "READY_FOR_REVIEW"
    STATE_LOCKED = "LOCKED"
    STATE_SUBMITTED = "SUBMITTED"

    def __init__(
        self, 
        filing_repo: FilingCaseRepository,
        itr_repo: ITRDeterminationRepository,
        audit_service: AuditService,
        evidence_service: EvidenceService,
        confirmation_repo: ConfirmationRepository
    ):
        self.filing_repo = filing_repo
        self.itr_repo = itr_repo
        self.audit_service = audit_service
        self.evidence_service = evidence_service
        self.confirmation_repo = confirmation_repo
        
        # Strict Forward-Only State Machine
        self._transitions: Dict[str, Set[str]] = {
            self.STATE_DRAFT: {self.STATE_REVIEW},
            self.STATE_REVIEW: {self.STATE_LOCKED}, # CA Mode: Needs Approval
            self.STATE_LOCKED: {self.STATE_SUBMITTED}, # CA Mode: Needs Confirmation
            self.STATE_SUBMITTED: set() # Terminal State
        }

    async def get_case(self, session: AsyncSession, user_id: UUID, financial_year: str) -> Optional[FilingCase]:
        """
        Retrieve a filing case.
        """
        return await self.filing_repo.get_by_user_and_year(session, user_id, financial_year)

    async def create_case(
        self, 
        session: AsyncSession, 
        user_id: UUID, 
        financial_year: str, 
        itr_determination_id: UUID,
        actor_role: str = "SYSTEM" # Default if not provided, but mostly called by user action
    ) -> FilingCase:
        """
        Initialize a new filing case in DRAFT state.
        Raises ValidationError if case already exists or ITR determination is invalid.
        """
        # 1. Validate ITR Determination
        determination = await self.itr_repo.get_by_id(session, itr_determination_id)
        
        if not determination:
            raise NotFoundError("ITR Determination not found")
        
        if determination.user_id != user_id:
                raise ValidationError("ITR Determination does not belong to this user")

        if determination.financial_year != financial_year:
            raise ValidationError("ITR Determination financial year mismatch")

        if not determination.is_locked:
            raise ValidationError("ITR Determination must be LOCKED before creating a Filing Case")

        # 2. Check Existence of Filing Case
        existing = await self.filing_repo.get_by_user_and_year(session, user_id, financial_year)
        if existing:
            raise ValidationError(f"Filing Case already exists for {financial_year}")

        # 3. Create New Case
        new_case = FilingCase(
            user_id=user_id,
            financial_year=financial_year,
            itr_determination_id=itr_determination_id,
            current_state=self.STATE_DRAFT,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        created_case = await self.filing_repo.create_case(session, new_case)
        
        # 4. Audit Log
        await self.audit_service.log_action(
            session=session,
            actor_id=user_id,
            actor_role=actor_role,
            action="FILING_CASE_CREATED",
            after_value={
                "id": str(created_case.id),
                "financial_year": financial_year,
                "itr_determination_id": str(itr_determination_id),
                "current_state": self.STATE_DRAFT
            }
        )
        
        return created_case

    async def approve_filing(
        self,
        session: AsyncSession,
        filing_id: UUID,
        user_id: UUID,
        ip_address: Optional[str] = None
    ) -> FilingCase:
        """
        Taxpayer Action: Approve the Filing.
        Transitions state to LOCKED.
        Creates UserConfirmation record.
        """
        # 1. Fetch
        case = await self.filing_repo.get_by_id(session, filing_id)
        if not case:
             raise NotFoundError("Filing Case not found")

        # 2. Validate Ownership
        if case.user_id != user_id:
             raise UnauthorizedError("Unauthorized: Only the taxpayer can approve this filing")

        # 3. Validate State
        if case.current_state != self.STATE_REVIEW:
             raise ValidationError("Filing is not ready for approval")

        # 4. Create Confirmation Artifact
        confirmation = UserConfirmation(
            filing_id=filing_id,
            confirmation_type="FILING_APPROVAL",
            confirmed_by=user_id,
            ip_address=ip_address,
            confirmed_at=datetime.now(timezone.utc)
        )
        
        await self.confirmation_repo.create_confirmation(session, confirmation)
        
        # 5. Transition to LOCKED (via internal helper to reuse logic/audit)
        # We manually call transition here because this IS the transition
        before_value = {"id": str(case.id), "current_state": case.current_state}
        
        updates = {
             "current_state": self.STATE_LOCKED,
             "updated_at": datetime.now(timezone.utc)
        }
        
        updated_case = await self.filing_repo.update_case(session, case, updates)

        # 6. Capture Evidence of Approval
        await self.evidence_service.capture_evidence(
            session=session,
            payload={
                "filing_id": str(updated_case.id),
                "action": "TAXPAYER_APPROVAL",
                "confirmed_by": str(user_id),
                "ip_address": ip_address,
                "timestamp": confirmation.confirmed_at.isoformat()
            },
            action_urn=f"urn:filing:{updated_case.id}:approval"
        )
        
        # 7. Audit Log
        await self.audit_service.log_action(
            session=session,
            actor_id=user_id,
            actor_role="INDIVIDUAL", # Taxpayer is always INDIVIDUAL/BUSINESS owner
            action="FILING_APPROVED",
            before_value=before_value,
            after_value={"id": str(updated_case.id), "current_state": self.STATE_LOCKED}
        )
        
        return updated_case


    async def transition_state(
        self, 
        session: AsyncSession, 
        filing_id: UUID,
        actor_id: UUID, 
        next_state: str,
        actor_role: str
    ) -> FilingCase:
        """
        Move the case to the next state.
        Enforces Strict State Machine Logic.
        """
        # 1. Fetch
        case = await self.filing_repo.get_by_id(session, filing_id)
        if not case:
            raise NotFoundError("Filing Case not found")

        # 2. Strict Role Enforcement & Transitions
        current_state = case.current_state

        # A. DRAFT -> READY_FOR_REVIEW
        if current_state == self.STATE_DRAFT and next_state == self.STATE_REVIEW:
            if case.filing_mode == "CA":
                 if actor_role != "CA":
                      raise UnauthorizedError("Only Assigned CA can mark filing as Ready for Review")
            elif case.filing_mode == "SELF":
                 if actor_id != case.user_id:
                      raise UnauthorizedError("Only the Taxpayer can transition Self-Filing")

        # B. READY_FOR_REVIEW -> LOCKED
        elif current_state == self.STATE_REVIEW and next_state == self.STATE_LOCKED:
            if case.filing_mode == "CA":
                # This transition MUST happen via approve_filing, but if called directly:
                if actor_id != case.user_id:
                     raise UnauthorizedError("Only Taxpayer can approve/lock the filing")
            elif case.filing_mode == "SELF":
                if actor_id != case.user_id:
                     raise UnauthorizedError("Only Taxpayer can lock Self-Filing")

        # C. LOCKED -> SUBMITTED
        elif current_state == self.STATE_LOCKED and next_state == self.STATE_SUBMITTED:
             if case.filing_mode == "CA":
                 if actor_role != "CA":
                     raise UnauthorizedError("Only Assigned CA can submit CA-managed filing")
             elif case.filing_mode == "SELF":
                 if actor_id != case.user_id:
                     raise UnauthorizedError("Only Taxpayer can submit Self-Filing")

        # D. General/Unauthorized Intermediate Checks
        else:
             # Prevent arbitrary jumps or unauthorized roles for other theoretical transitions
             pass # Logic covered by strict state machine below

        
        # 3. Validate Transition Path
        allowed_next = self._transitions.get(current_state, set())
        
        if next_state not in allowed_next:
            raise ValidationError(f"Invalid transition from {current_state} to {next_state}")

        # CA Workflow Enforcement: SUBMITTED requires LOCKED state + Confirmation
        if next_state == self.STATE_SUBMITTED and case.filing_mode == "CA":
                if current_state != self.STATE_LOCKED:
                    raise ValidationError("CA Filing must be LOCKED (Approved) before submission")
                
                # Check Confirmation
                confirmation = await self.confirmation_repo.get_latest_by_filing(session, case.id)
                if not confirmation:
                    raise ValidationError("Missing Taxpayer Approval Confirmation for this filing")
                
                submission_confirmation_ref = str(confirmation.id)
        else:
                submission_confirmation_ref = None


        # Capture state before update
        before_value = {
            "id": str(case.id),
            "current_state": current_state
        }

        # 4. Apply Updates
        updates = {
            "current_state": next_state,
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Special handling for submission
        if next_state == self.STATE_SUBMITTED:
            updates["submitted_at"] = datetime.now(timezone.utc)

        updated_case = await self.filing_repo.update_case(session, case, updates)
        
        # Evidence Capture (Atomic) for SUBMISSION
        if next_state == self.STATE_SUBMITTED:
            determination = await self.itr_repo.get_by_id(session, case.itr_determination_id)
            await self.evidence_service.capture_evidence(
                session=session,
                payload={
                    "filing_case": {
                        "id": str(updated_case.id),
                        "financial_year": updated_case.financial_year,
                        "submitted_at": updated_case.submitted_at.isoformat() if updated_case.submitted_at else None,
                    },
                    "itr_determination": {
                        "id": str(determination.id) if determination else None,
                        "itr_type": determination.itr_type if determination else None
                    },
                    "actor_id": str(actor_id),
                    "actor_role": actor_role,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "confirmation_ref": submission_confirmation_ref # Link to approval
                },
                action_urn=f"urn:filing:{updated_case.id}:submission",
                retention_years=7
            )
        
        # 5. Audit Log
        await self.audit_service.log_action(
            session=session,
            actor_id=actor_id,
            actor_role=actor_role,
            action="FILING_STATE_TRANSITION",
            before_value=before_value,
            after_value={
                "id": str(updated_case.id),
                "current_state": next_state,
                "previous_state": current_state
            }
        )

        return updated_case

