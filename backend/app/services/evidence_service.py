import json
import hashlib
from datetime import datetime, timedelta, date, timezone
from typing import Any, Dict, Union
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evidence import EvidenceRecord
from app.repositories.evidence_repository import EvidenceRepository
from app.services.file_storage_service import FileStorageService

class EvidenceService:
    """
    Service for capturing and verifying evidence.
    Core Logic: Canonicalization, Hashing, Persistence.
    """
    def __init__(
        self, 
        repo: EvidenceRepository, 
        storage_service: FileStorageService
    ):
        self.repo = repo
        self.storage_service = storage_service

    def _canonicalize(self, payload: Union[Dict[str, Any], BaseModel]) -> bytes:
        """
        Deterministic JSON serialization.
        - Sorts keys
        - UTF-8 encoding
        - Ensures no whitespace around separators
        """
        if isinstance(payload, BaseModel):
            data = payload.model_dump(mode='json')
        else:
            data = payload

        # sort_keys=True is critical for deterministic hashing
        json_str = json.dumps(
            data, 
            sort_keys=True, 
            ensure_ascii=False, 
            separators=(',', ':')
        )
        return json_str.encode('utf-8')

    def _compute_hash(self, data: bytes) -> str:
        """
        SHA-256 Hash of bytes.
        """
        return hashlib.sha256(data).hexdigest()

    async def capture_evidence(
        self,
        session: AsyncSession,
        payload: Union[Dict[str, Any], BaseModel],
        action_urn: str,
        retention_years: int = 5
    ) -> EvidenceRecord:
        """
        Capture a new Evidence Record.
        
        Args:
            session: AsyncSession (Transaction Managed by Caller)
            payload: Data to be signed/stored
            action_urn: Unique identifier for the action (urn:entity:id:action)
            retention_years: Policy duration (default 5)
        
        Returns:
            Peristed EvidenceRecord ORM object.
        """
        # 1. Canonicalize & Hash
        canonical_bytes = self._canonicalize(payload)
        file_hash = self._compute_hash(canonical_bytes)
        
        # 2. Determine Retention
        expiry_date = date.today() + timedelta(days=365 * retention_years)
        
        # 3. Determine Storage Path
        # Structure: evidence/{YYYY}/{MM}/{hash}.json
        now = datetime.now(timezone.utc)
        relative_path = f"evidence/{now.year}/{now.month:02d}/{file_hash}.json"
        
        # 4. Write Blob (File System)
        await self.storage_service.write_blob(relative_path, canonical_bytes)
        
        # 5. Persist Metadata (Database)
        evidence = EvidenceRecord(
            related_action=action_urn,
            hash=file_hash,
            storage_location=relative_path,
            retention_expiry=expiry_date
        )
        
        return await self.repo.create_record(session, evidence)
