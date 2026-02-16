from datetime import datetime, timezone
from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.consent import ConsentArtifact, ConsentAuditLog
from app.models.consent import ConsentArtifact, ConsentAuditLog
from app.repositories.consent_repository import ConsentRepository, ConsentAuditRepository
from app.core.exceptions import NotFoundError, UnauthorizedError, ValidationError

from app.services.evidence_service import EvidenceService

class ConsentService:
    """
    Manages Consent Lifecycle.
    Enforces business rules for data access and delegation.
    Transactions are managed by the caller.
    """
    def __init__(
        self,
        consent_repo: ConsentRepository,
        audit_repo: ConsentAuditRepository,
        evidence_service: EvidenceService
    ):
        self.consent_repo = consent_repo
        self.audit_repo = audit_repo
        self.evidence_service = evidence_service

    async def grant_consent(
        self,
        session: AsyncSession,
        user_id: UUID,
        purpose: str,
        scope: str,
        expiry_at: datetime
    ) -> ConsentArtifact:
        """
        Grants a new consent.
        Valdiates expiry is in the future.
        """
        if expiry_at <= datetime.now(timezone.utc):
            raise ValidationError("Expiry must be in the future")

        consent = ConsentArtifact(
            user_id=user_id,
            purpose=purpose,
            scope=scope,
            expiry_at=expiry_at,
            status="ACTIVE",
            granted_at=datetime.now(timezone.utc)
        )
        
        created_consent = await self.consent_repo.create_consent(session, consent)
        
        # Evidence Capture (Atomic)
        await self.evidence_service.capture_evidence(
            session=session,
            payload=created_consent, # Pydantic/ORM model handling in service
            action_urn=f"urn:consent:{created_consent.id}:grant"
        )
        
        # Audit Log
        await self.audit_repo.create_log(session, ConsentAuditLog(
            consent_id=created_consent.id,
            action="GRANTED",
            actor_id=user_id,
            reason=f"Purpose: {purpose}"
        ))
        
        return created_consent

    async def revoke_consent(
        self,
        session: AsyncSession,
        consent_id: UUID,
        user_id: UUID,
        reason: str
    ) -> None:
        """
        Revokes an existing consent.
        Ensures ownership.
        """
        consent = await self.consent_repo.get_by_id(session, consent_id)
        if not consent:
            raise NotFoundError("Consent not found")
        
        if consent.user_id != user_id:
            raise UnauthorizedError("Unauthorized to revoke this consent")
            
        if consent.status != "ACTIVE":
            raise ValidationError("Consent is not active")

        await self.consent_repo.update_status(session, consent_id, "REVOKED")
        
        # Evidence Capture (Atomic)
        await self.evidence_service.capture_evidence(
            session=session,
            payload={
                "consent_id": str(consent_id),
                "revoked_by": str(user_id),
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            action_urn=f"urn:consent:{consent_id}:revoke"
        )
        
        # Audit Log
        await self.audit_repo.create_log(session, ConsentAuditLog(
            consent_id=consent_id,
            action="REVOKED",
            actor_id=user_id,
            reason=reason
        ))
