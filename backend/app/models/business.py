from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, Date, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text

from .base import Base

class BusinessProfile(Base):
    __tablename__ = "business_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Legal Identity
    constitution_type = Column(String, nullable=False)
    business_name = Column(Text, nullable=False)
    date_of_incorporation = Column(Date, nullable=False)

    # Registration Status
    # Removed defaults to enforce explicit assignment in Service Layer
    gst_registered = Column(Boolean, nullable=False)
    gstin = Column(String, nullable=True)
    tan_available = Column(Boolean, nullable=False)
    msme_registered = Column(Boolean, nullable=False)
    iec_available = Column(Boolean, nullable=False)

    # Operational Snapshot
    turnover_bracket = Column(String, nullable=False)
    books_maintained = Column(Boolean, nullable=False)
    accounting_method = Column(String, nullable=False)

    # Location
    registered_state = Column(String, nullable=False)

    # Meta
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="business_profile")
