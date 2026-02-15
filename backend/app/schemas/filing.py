from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, constr

# Regex for YYYY-YY
YEAR_REGEX = r"^\d{4}-\d{2}$"

class FilingCaseCreate(BaseModel):
    financial_year: str = Field(..., pattern=YEAR_REGEX, description="Financial Year (e.g., 2025-26)")
    itr_determination_id: UUID

class FilingCaseTransition(BaseModel):
    next_state: str = Field(..., min_length=1, max_length=30)

class FilingCaseResponse(BaseModel):
    id: UUID
    user_id: UUID
    financial_year: str
    itr_determination_id: UUID
    current_state: str
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime] = None

    class Config:
        from_attributes = True
