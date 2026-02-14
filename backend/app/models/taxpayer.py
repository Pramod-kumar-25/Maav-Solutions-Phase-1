from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, DateTime, text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import func
from .base import Base
import enum

class ResidentialStatus(str, enum.Enum):
    """
    Python-level Enum for Residential Status.
    Snapshot stored as String in DB.
    """
    RESIDENT = "RESIDENT"
    RNOR = "RNOR"
    NRI = "NRI"

class TaxpayerProfile(Base):
    __tablename__ = "taxpayer_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Classification Snapshot
    residential_status = Column(String(20), nullable=True) 

    # Defaults
    default_tax_regime = Column(String(20), nullable=False, server_default=text("'NEW'"))
    aadhaar_link_status = Column(Boolean, nullable=False, server_default=text("false"))
    
    # Classification Inputs
    days_in_india_current_fy = Column(Integer, nullable=True)
    days_in_india_last_4_years = Column(Integer, nullable=True)
    # Note: server_default removed here to match DB state (it was dropped in migration)
    has_foreign_income = Column(Boolean, nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "residential_status IN ('RESIDENT', 'RNOR', 'NRI')",
            name="check_residential_status"
        ),
    )

    # Relationships
    user = relationship("User", back_populates="taxpayer_profile")

    @hybrid_property
    def pan_type(self) -> str:
        """
        Derives PAN Type from the 4th character of the User's PAN.
        Format: XXXXX1234X
        Index 3 (0-based) is the status.
        P = Individual, C = Company, etc.
        """
        if self.user and self.user.pan and len(self.user.pan) >= 4:
            return self.user.pan[3].upper()
        return "UNKNOWN"
