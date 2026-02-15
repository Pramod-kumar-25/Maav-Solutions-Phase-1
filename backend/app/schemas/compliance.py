from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class ComplianceEvaluationRequest(BaseModel):
    financial_year: str = Field(..., description="Financial Year to evaluate (e.g., 2024-25)", pattern=r"^\d{4}-\d{2}$")

class ComplianceResolutionRequest(BaseModel):
    resolution_notes: Optional[str] = Field(None, description="Notes explaining the resolution")

class ComplianceFlagResponse(BaseModel):
    id: UUID
    user_id: UUID
    financial_year: str
    flag_code: str
    description: str
    severity: str
    is_resolved: bool
    resolved_at: Optional[datetime]
    resolution_notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
