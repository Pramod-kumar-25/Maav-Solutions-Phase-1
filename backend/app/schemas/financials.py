from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, Literal
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
import re

class FinancialEntryCreate(BaseModel):
    entry_type: Literal['INCOME', 'EXPENSE']
    category: str = Field(..., min_length=1, max_length=100)
    amount: Decimal = Field(..., ge=0, decimal_places=2)
    financial_year: str = Field(..., pattern=r'^\d{4}-\d{2}$')
    entry_date: date
    description: Optional[str] = None

    @field_validator('financial_year')
    @classmethod
    def validate_fy(cls, v: str) -> str:
        # Simple logical check for FY (e.g., 2024-25)
        # Part 1: YYYY, Part 2: YY
        parts = v.split('-')
        year_start = int(parts[0])
        year_end_suffix = int(parts[1])
        
        # Check if year_end_suffix matches year_start + 1
        expected_suffix = (year_start + 1) % 100
        if year_end_suffix != expected_suffix:
            raise ValueError(f"Invalid Financial Year range. For {year_start}, suffix should be {expected_suffix:02d}")
        
        return v

class FinancialEntryResponse(BaseModel):
    id: UUID
    user_id: UUID
    entry_type: str
    category: str
    amount: Decimal
    financial_year: str
    entry_date: date
    description: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
