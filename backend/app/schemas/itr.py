from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class ITRDeterminationRequest(BaseModel):
    financial_year: str = Field(..., description="Financial Year (e.g., 2024-25)", pattern=r"^\d{4}-\d{2}$")

class ITRDeterminationResponse(BaseModel):
    id: UUID
    user_id: UUID
    financial_year: str
    itr_type: str
    reason: str
    is_locked: bool
    determined_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True
