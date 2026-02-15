from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from uuid import UUID
from typing import List, Dict, Any
from app.models.financials import FinancialEntry

class FinancialEntryRepository:
    """
    Repository for Unified Financial Ledger.
    Handles persistence for FinancialEntry (Income & Expenses).
    """

    async def create_entry(self, session: AsyncSession, user_id: UUID, entry_data: Dict[str, Any]) -> FinancialEntry:
        """
        Create a new financial entry (Income or Expense).
        entry_data: Dictionary containing fields like entry_type, amount, category, etc.
        """
        entry = FinancialEntry(user_id=user_id, **entry_data)
        session.add(entry)
        await session.flush()
        await session.refresh(entry)
        return entry

    async def get_by_user_id(self, session: AsyncSession, user_id: UUID) -> List[FinancialEntry]:
        """
        Retrieve all financial entries for a specific user, ordered by date descending.
        """
        stmt = select(FinancialEntry).where(FinancialEntry.user_id == user_id).order_by(FinancialEntry.entry_date.desc())
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_user_id_and_type(self, session: AsyncSession, user_id: UUID, entry_type: str) -> List[FinancialEntry]:
        """
        Retrieve entries filtered by type (INCOME / EXPENSE) for a specific user.
        """
        stmt = select(FinancialEntry).where(
            FinancialEntry.user_id == user_id,
            FinancialEntry.entry_type == entry_type
        ).order_by(FinancialEntry.entry_date.desc())
        
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, session: AsyncSession, entry_id: UUID) -> FinancialEntry | None:
        """
        Retrieve a financial entry by its ID.
        """
        stmt = select(FinancialEntry).where(FinancialEntry.id == entry_id)
        result = await session.execute(stmt)
        return result.scalars().first()

    async def delete_entry_by_id(self, session: AsyncSession, entry_id: UUID) -> bool:
        """
        Delete a financial entry by its ID.
        Returns True if a record was deleted, False otherwise.
        """
        stmt = delete(FinancialEntry).where(FinancialEntry.id == entry_id)
        result = await session.execute(stmt)
        return result.rowcount > 0
