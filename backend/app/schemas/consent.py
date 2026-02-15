from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class ConsentCreate(BaseModel):
    purpose: str
    scope: str
    expiry_at: datetime
    consent_version: Optional[str] = None

class ConsentResponse(BaseModel):
    id: UUID
    purpose: str
    scope: str
    status: str
    expiry_at: datetime
    granted_at: datetime
    model_config = ConfigDict(from_attributes=True)

class CAAssignmentCreate(BaseModel):
    filing_id: UUID
    ca_user_id: UUID
    consent_id: UUID

class CAAssignmentResponse(BaseModel):
    id: UUID
    filing_id: UUID
    ca_user_id: UUID
    consent_id: UUID
    status: str
    assigned_at: datetime
    model_config = ConfigDict(from_attributes=True)
