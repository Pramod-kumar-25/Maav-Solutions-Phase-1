from pydantic import BaseModel, Field, root_validator
from typing import Optional
from uuid import UUID
from datetime import datetime

class TaxpayerProfileBase(BaseModel):
    days_in_india_current_fy: int = Field(..., ge=0, description="Days spent in India in the current Financial Year")
    days_in_india_last_4_years: Optional[int] = Field(0, ge=0, description="Total days spent in India over the last 4 Financial Years")
    has_foreign_income: bool = Field(False, description="Whether the taxpayer has income from foreign sources")
    default_tax_regime: str = Field("NEW", description="Preferred Tax Regime (NEW/OLD)")
    aadhaar_link_status: bool = Field(False, description="Is PAN linked with Aadhaar?")

class TaxpayerProfileCreate(TaxpayerProfileBase):
    pass

class TaxpayerProfileUpdate(TaxpayerProfileBase):
    pass

class TaxpayerProfileResponse(TaxpayerProfileBase):
    id: UUID
    user_id: UUID
    residential_status: str
    created_at: datetime
    pan_type: str  # Derived property

    class Config:
        from_attributes = True
