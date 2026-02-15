from uuid import UUID
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.filing import FilingCase

class FilingCaseRepository:
    """
    Filing Case Repository.
    Handles persistence for Filing Case Workflow.
    Strictly no business logic.
    """

    async def get_by_user_and_year(self, session: AsyncSession, user_id: UUID, financial_year: str) -> Optional[FilingCase]:
        """
        Retrieve Filing Case for a specific user and financial year.
        """
        result = await session.execute(
            select(FilingCase).where(
                FilingCase.user_id == user_id,
                FilingCase.financial_year == financial_year
            )
        )
        return result.scalars().first()

    async def create_case(self, session: AsyncSession, filing_case: FilingCase) -> FilingCase:
        """
        Persist a new Filing Case.
        """
        session.add(filing_case)
        await session.flush()
        await session.refresh(filing_case)
        return filing_case

    async def update_case(self, session: AsyncSession, filing_case: FilingCase, updated_data: Dict[str, Any]) -> FilingCase:
        """
        Update an existing Filing Case.
        """
        for field, value in updated_data.items():
            setattr(filing_case, field, value)
        
        await session.flush()
        await session.refresh(filing_case)
        return filing_case
