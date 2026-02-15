from typing import List, Type, Set, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.compliance import ComplianceFlagResponse

from app.repositories.financial_repository import FinancialEntryRepository
from app.repositories.compliance_repository import ComplianceFlagRepository
from app.services.compliance_rules import (
    BaseComplianceRule,
    HighTotalExpenseRule,
    ExpenseWithoutIncomeRule
)

class ComplianceEngineService:
    """
    Orchestrates deterministic compliance checks.
    """

    def __init__(
        self,
        financial_repo: FinancialEntryRepository,
        compliance_repo: ComplianceFlagRepository
    ):
        self.financial_repo = financial_repo
        self.compliance_repo = compliance_repo
        # Static Registry of Rules - Deterministic Order
        self.rules: List[Type[BaseComplianceRule]] = [
            HighTotalExpenseRule,
            ExpenseWithoutIncomeRule
        ]

    async def evaluate_user(self, session: AsyncSession, user_id: UUID, financial_year: str) -> None:
        """
        Evaluate all registered rules for a user for a specific financial year.
        Persists flags if violations are found.
        Idempotent: Checks for existing unresolved flags to prevent duplicates.
        """
        # 1. Fetch Data (Pure Data for Rules)
        entries = await self.financial_repo.get_by_user_id_and_year(session, user_id, financial_year)
        
        # 2. Fetch Existing Flags (Optimization: Fetch once)
        existing_flags = await self.compliance_repo.get_by_user_id_and_year(session, user_id, financial_year)
        
        # Build set of unresolved flag codes
        # Logic: If an unresolved flag exists for this code, we do NOT recreate it.
        # If a resolved flag exists, we DO recreate it (recurrence).
        existing_unresolved_codes: Set[str] = {
            f.flag_code for f in existing_flags if not f.is_resolved
        }

        # 3. Explicit Transaction Block for Writes
        async with session.begin():
            # 4. Iterate and Evaluate
            for RuleClass in self.rules:
                rule = RuleClass()
                violation = rule.evaluate(entries)

                if violation:
                    flag_code = violation['flag_code']
                    
                    # 5. Check for Duplicates
                    if flag_code not in existing_unresolved_codes:
                        # Persist Flag
                        flag_data = {
                            "financial_year": financial_year,
                            "flag_code": flag_code,
                            "description": violation['description'],
                            "severity": violation['severity']
                        }
                        await self.compliance_repo.create_flag(session, user_id, flag_data)
                        
                        # Add to local set to prevent duplicate inserts within same request (unlikely but safe)
                        existing_unresolved_codes.add(flag_code)

    async def get_user_flags(self, session: AsyncSession, user_id: UUID, financial_year: str | None = None) -> List[ComplianceFlagResponse]: # Type hint will need import or just 'list'
        """
        Retrieve compliance flags for a user.
        """
        if financial_year:
            return await self.compliance_repo.get_by_user_id_and_year(session, user_id, financial_year)
        return await self.compliance_repo.get_by_user_id(session, user_id)

    async def resolve_flag(self, session: AsyncSession, user_id: UUID, flag_id: UUID, notes: str | None) -> ComplianceFlagResponse:
        """
        Resolve a flag. Enforces ownership.
        """
        async with session.begin():
            # 1. Fetch Flag
            flag = await self.compliance_repo.get_by_id(session, flag_id)
            
            if not flag:
                raise ValueError("Flag not found")
                
            if flag.user_id != user_id:
                raise ValueError("Unauthorized to resolve this flag")
                
            # 2. Mark Resolved
            return await self.compliance_repo.mark_resolved(session, flag_id, notes)
