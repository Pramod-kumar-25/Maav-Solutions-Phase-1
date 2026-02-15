from datetime import datetime, timezone
from typing import Optional, Dict, Set
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.filing import FilingCase
from app.repositories.filing_repository import FilingCaseRepository
from app.repositories.itr_repository import ITRDeterminationRepository

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
        itr_repo: ITRDeterminationRepository
    ):
        self.filing_repo = filing_repo
        self.itr_repo = itr_repo
        
        # Strict Forward-Only State Machine
        self._transitions: Dict[str, Set[str]] = {
            self.STATE_DRAFT: {self.STATE_REVIEW},
            self.STATE_REVIEW: {self.STATE_LOCKED},
            self.STATE_LOCKED: {self.STATE_SUBMITTED},
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
        itr_determination_id: UUID
    ) -> FilingCase:
        """
        Initialize a new filing case in DRAFT state.
        Raises ValueError if case already exists or ITR determination is invalid.
        """
        async with session.begin():
            # 1. Validate ITR Determination
            determination = await self.itr_repo.get_by_id(session, itr_determination_id)
            
            if not determination:
                raise ValueError("ITR Determination not found")
            
            if determination.user_id != user_id:
                 raise ValueError("ITR Determination does not belong to this user")

            if determination.financial_year != financial_year:
                raise ValueError("ITR Determination financial year mismatch")

            if not determination.is_locked:
                raise ValueError("ITR Determination must be LOCKED before creating a Filing Case")

            # 2. Check Existence of Filing Case
            existing = await self.filing_repo.get_by_user_and_year(session, user_id, financial_year)
            if existing:
                raise ValueError(f"Filing Case already exists for {financial_year}")

            # 3. Create New Case
            new_case = FilingCase(
                user_id=user_id,
                financial_year=financial_year,
                itr_determination_id=itr_determination_id,
                current_state=self.STATE_DRAFT,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            return await self.filing_repo.create_case(session, new_case)

    async def transition_state(
        self, 
        session: AsyncSession, 
        user_id: UUID, 
        financial_year: str, 
        next_state: str
    ) -> FilingCase:
        """
        Move the case to the next state.
        Enforces Strict State Machine Logic.
        """
        async with session.begin():
            # 1. Fetch
            case = await self.filing_repo.get_by_user_and_year(session, user_id, financial_year)
            if not case:
                raise ValueError("Filing Case not found")

            # 2. Validate Transition
            current_state = case.current_state
            allowed_next = self._transitions.get(current_state, set())
            
            if next_state not in allowed_next:
                raise ValueError(f"Invalid transition from {current_state} to {next_state}")

            # 3. Apply Updates
            updates = {
                "current_state": next_state,
                "updated_at": datetime.now(timezone.utc)
            }
            
            # Special handling for submission
            if next_state == self.STATE_SUBMITTED:
                updates["submitted_at"] = datetime.now(timezone.utc)

            return await self.filing_repo.update_case(session, case, updates)
