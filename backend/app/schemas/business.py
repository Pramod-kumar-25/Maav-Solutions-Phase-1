from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import date, datetime

class BusinessProfileBase(BaseModel):
    # Legal Identity
    constitution_type: str = Field(..., description="Legal constitution (e.g., PROPRIETORSHIP, COMPANY)")
    business_name: str = Field(..., description="Registered Business Name")
    date_of_incorporation: date = Field(..., description="Date of Incorporation/Formation")

    # Registration Status
    gst_registered: bool = Field(False)
    gstin: Optional[str] = Field(None, description="GSTIN if registered")
    tan_available: bool = Field(False)
    msme_registered: bool = Field(False)
    iec_available: bool = Field(False)

    # Operational Snapshot
    turnover_bracket: str = Field(..., description="Annual Turnover Bracket")
    books_maintained: bool = Field(False)
    accounting_method: str = Field(..., description="CASH or MERCANTILE")

    # Location
    registered_state: str = Field(..., description="State of Registration")

class BusinessProfileCreate(BusinessProfileBase):
    pass

class BusinessProfileUpdate(BusinessProfileBase):
    pass

class BusinessProfileResponse(BusinessProfileBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True
