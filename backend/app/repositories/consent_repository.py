from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.consent import ConsentArtifact, CAAssignment, ConsentAuditLog

class ConsentRepository:
    """
    Repository for Consent Artifacts.
    """
    async def create_consent(self, session: AsyncSession, consent: ConsentArtifact) -> ConsentArtifact:
        session.add(consent)
        await session.flush()
        await session.refresh(consent)
        return consent

    async def get_by_id(self, session: AsyncSession, consent_id: UUID) -> Optional[ConsentArtifact]:
        result = await session.execute(
            select(ConsentArtifact).where(ConsentArtifact.id == consent_id)
        )
        return result.scalars().first()

    async def get_by_user(self, session: AsyncSession, user_id: UUID) -> List[ConsentArtifact]:
        result = await session.execute(
            select(ConsentArtifact).where(ConsentArtifact.user_id == user_id)
        )
        return list(result.scalars().all())

    async def update_status(self, session: AsyncSession, consent_id: UUID, new_status: str) -> None:
        consent = await self.get_by_id(session, consent_id)
        if consent:
            consent.status = new_status
            await session.flush()

class CAAssignmentRepository:
    """
    Repository for CA Assignments.
    """
    async def create_assignment(self, session: AsyncSession, assignment: CAAssignment) -> CAAssignment:
        session.add(assignment)
        await session.flush()
        await session.refresh(assignment)
        return assignment

    async def get_by_filing_id(self, session: AsyncSession, filing_id: UUID) -> Optional[CAAssignment]:
        result = await session.execute(
            select(CAAssignment).where(CAAssignment.filing_id == filing_id)
        )
        return result.scalars().first()

    async def get_by_ca_user(self, session: AsyncSession, ca_user_id: UUID) -> List[CAAssignment]:
        result = await session.execute(
            select(CAAssignment).where(CAAssignment.ca_user_id == ca_user_id)
        )
        return list(result.scalars().all())

    async def update_status(self, session: AsyncSession, assignment_id: UUID, new_status: str) -> None:
        # Fetch directly to update
        result = await session.execute(
             select(CAAssignment).where(CAAssignment.id == assignment_id)
        )
        assignment = result.scalars().first()
        if assignment:
            assignment.status = new_status
            await session.flush()

class ConsentAuditRepository:
    """
    Repository for Consent Audit Logs.
    """
    async def create_log(self, session: AsyncSession, log: ConsentAuditLog) -> ConsentAuditLog:
        session.add(log)
        await session.flush()
        await session.refresh(log)
        return log

    async def get_by_consent(self, session: AsyncSession, consent_id: UUID) -> List[ConsentAuditLog]:
        result = await session.execute(
            select(ConsentAuditLog).where(ConsentAuditLog.consent_id == consent_id).order_by(ConsentAuditLog.created_at)
        )
        return list(result.scalars().all())
