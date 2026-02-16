from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.evidence import EvidenceRecord

class EvidenceRepository:
    """
    Repository for EvidenceRecord entity.
    Pure Data Access Layer. No business logic.
    """
    
    async def create_record(self, session: AsyncSession, evidence: EvidenceRecord) -> EvidenceRecord:
        """
        Persist a new Evidence Record.
        Transaction management is handled by the caller.
        """
        session.add(evidence)
        await session.flush()
        await session.refresh(evidence)
        return evidence

    async def get_by_id(self, session: AsyncSession, evidence_id: UUID) -> Optional[EvidenceRecord]:
        """
        Retrieve Evidence Record by ID.
        """
        result = await session.execute(
            select(EvidenceRecord).where(EvidenceRecord.id == evidence_id)
        )
        return result.scalar_one_or_none()

    async def get_by_related_action(self, session: AsyncSession, action_urn: str) -> Optional[EvidenceRecord]:
        """
        Retrieve Evidence Record by its related action URN.
        """
        result = await session.execute(
            select(EvidenceRecord).where(EvidenceRecord.related_action == action_urn)
        )
        return result.scalars().first()
