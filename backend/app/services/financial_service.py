from typing import List, Dict, Any
from uuid import UUID
import re
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.financial_repository import FinancialEntryRepository
from app.repositories.auth_repository import AuthRepository
from app.models.financials import FinancialEntry

class FinancialEntryService:
    def __init__(self, financial_repo: FinancialEntryRepository, auth_repo: AuthRepository):
        self.financial_repo = financial_repo
        self.auth_repo = auth_repo

    async def create_entry(self, session: AsyncSession, user_id: UUID, entry_data: Dict[str, Any]) -> FinancialEntry:
        """
        Create a new financial entry.
        
        Validations:
        1. User must exist.
        2. entry_type must be 'INCOME' or 'EXPENSE'.
        3. financial_year must follow 'YYYY-YY' pattern.
        """
        
        # 1. Validate User Existence
        user = await self.auth_repo.get_user_by_id(session, user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found.")

        # 2. Validate Entry Type
        entry_type = entry_data.get('entry_type')
        if entry_type not in ['INCOME', 'EXPENSE']:
            raise ValueError(f"Invalid entry_type '{entry_type}'. Must be 'INCOME' or 'EXPENSE'.")

        # 3. Validate Financial Year Format (YYYY-YY)
        financial_year = entry_data.get('financial_year')
        if not financial_year or not re.match(r'^\d{4}-\d{2}$', financial_year):
            raise ValueError(f"Invalid financial_year format '{financial_year}'. Must be 'YYYY-YY'.")

        # 4. Create Entry in Transaction
        async with session.begin():
            new_entry = await self.financial_repo.create_entry(session, user_id, entry_data)
            return new_entry

    async def get_user_entries(self, session: AsyncSession, user_id: UUID) -> List[FinancialEntry]:
        """
        Retrieve all financial entries for a user.
        """
        return await self.financial_repo.get_by_user_id(session, user_id)

    async def get_user_entries_by_type(self, session: AsyncSession, user_id: UUID, entry_type: str) -> List[FinancialEntry]:
        """
        Retrieve financial entries filtered by type.
        """
        if entry_type not in ['INCOME', 'EXPENSE']:
            raise ValueError(f"Invalid entry_type '{entry_type}'. Must be 'INCOME' or 'EXPENSE'.")
            
        return await self.financial_repo.get_by_user_id_and_type(session, user_id, entry_type)

    async def delete_entry(self, session: AsyncSession, user_id: UUID, entry_id: UUID) -> bool:
        """
        Delete a financial entry.
        Strictly enforces ownership: entry.user_id must match request user_id.
        """
        async with session.begin():
            # 1. Fetch Entry
            entry = await self.financial_repo.get_by_id(session, entry_id)
            if not entry:
                return False

            # 2. Check Ownership
            if entry.user_id != user_id:
                raise ValueError("Unauthorized access to financial entry.")

            # 3. Delete
            deleted = await self.financial_repo.delete_entry_by_id(session, entry_id)
            return deleted
