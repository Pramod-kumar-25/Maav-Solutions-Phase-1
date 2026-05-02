from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.itr import ITRDetermination
from app.repositories.financial_repository import FinancialEntryRepository
from app.repositories.itr_repository import ITRDeterminationRepository
from app.services.audit_service import AuditService

class ITRDeterminationService:
    """
    ITR Determination Engine.
    Orchestrates deterministic logic for ITR form selection.
    """
    
    # Controlled Category Sets
    BUSINESS_CATEGORIES = {'BUSINESS', 'PROFESSION', 'FREELANCE'}
    SALARY_CATEGORIES = {'SALARY', 'PENSION'}
    # Other is implicit (anything not in business/salary)

    def __init__(
        self,
        financial_repo: FinancialEntryRepository,
        itr_repo: ITRDeterminationRepository,
        audit_service: AuditService
    ):
        self.financial_repo = financial_repo
        self.itr_repo = itr_repo
        self.audit_service = audit_service

    async def determine_itr(self, session: AsyncSession, user_id: UUID, financial_year: str) -> ITRDetermination:
        """
        Determine the applicable ITR form based on financial entries.
        Wrap entire logic in a single transaction for consistency.
        """
        async with session.begin():
            # 1. Fetch Data
            entries = await self.financial_repo.get_by_user_id_and_year(session, user_id, financial_year)
            
            # 2. Analyze Income Sources
            has_business_income = False
            has_salary_income = False
            has_other_income = False
            
            for entry in entries:
                if entry.entry_type == 'INCOME':
                    # Normalize category
                    category = (entry.category or "").strip().upper()
                    
                    if category in self.BUSINESS_CATEGORIES:
                        has_business_income = True
                    elif category in self.SALARY_CATEGORIES:
                        has_salary_income = True
                    else:
                        has_other_income = True

            # 3. Apply Deterministic Rules
            itr_type = "ITR-1"
            reason = "Standard Salary/Interest Income case."

            if has_business_income:
                itr_type = "ITR-3"
                reason = "Business/Profession Income detected."
            elif has_salary_income and has_other_income:
                itr_type = "ITR-2"
                reason = "Salary and Other Sources (Non-Business) detected."
            elif has_salary_income:
                itr_type = "ITR-1"
                reason = "Salary Income only."
            elif has_other_income:
                 itr_type = "ITR-1"
                 reason = "Other Sources only (e.g. Interest/Dividends)."
            else:
                 itr_type = "ITR-1"
                 reason = "No income sources found. Defaulting to ITR-1."

            # 4. Check Existing Determination
            existing = await self.itr_repo.get_by_user_and_year(session, user_id, financial_year)

            if existing:
                if existing.is_locked:
                    raise ValueError("ITR Determination is locked")
                
                # Update Existing
                return await self.itr_repo.update_determination(session, existing, {
                    "itr_type": itr_type,
                    "reason": reason,
                    "determined_at": datetime.now(timezone.utc)
                })

            # 5. Create New
            new_determination = ITRDetermination(
                user_id=user_id,
                financial_year=financial_year,
                itr_type=itr_type,
                reason=reason,
                determined_at=datetime.now(timezone.utc),
                is_locked=False
            )
            
            return await self.itr_repo.create_determination(session, new_determination)

    async def get_determination(self, session: AsyncSession, user_id: UUID, financial_year: str) -> Optional[ITRDetermination]:
        """
        Retrieve existing ITR determination.
        """
        return await self.itr_repo.get_by_user_and_year(session, user_id, financial_year)

    async def lock_determination(
        self, 
        session: AsyncSession, 
        user_id: UUID, 
        financial_year: str,
        actor_role: str = "SYSTEM"
    ) -> ITRDetermination:
        """
        Lock an existing determination.
        Enforces ownership via get_by_user_and_year (implicitly checks user_id).
        """
        async with session.begin():
            existing = await self.itr_repo.get_by_user_and_year(session, user_id, financial_year)
            
            if not existing:
                raise ValueError("Determination not found")
            
            if existing.is_locked:
                raise ValueError("Determination is already locked")
            
            # Capture state before update
            before_value = {
                "id": str(existing.id),
                "is_locked": False,
                "itr_type": existing.itr_type
            }

            locked_determination = await self.itr_repo.update_determination(session, existing, {"is_locked": True})

            # Audit Log
            await self.audit_service.log_action(
                session=session,
                actor_id=user_id,
                actor_role=actor_role,
                action="ITR_LOCKED",
                before_value=before_value,
                after_value={
                    "id": str(locked_determination.id),
                    "is_locked": True,
                    "itr_type": locked_determination.itr_type
                }
            )

            return locked_determination
