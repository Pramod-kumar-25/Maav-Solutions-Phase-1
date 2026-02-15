from sqlalchemy import Column, String, Boolean, Text, DateTime, ForeignKey, CheckConstraint, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base

class ComplianceFlag(Base):
    """
    Deterministic Compliance Engine - Flag Entity.
    Stores violations found by the engine.
    """
    __tablename__ = "compliance_flags"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Financial Year (YYYY-YY format enforced by Engine, but good to have regex constraint here too if desired, 
    # though simplified to String for now as per prompt constraints "Constraint severity levels via CHECK")
    # We will assume regex validation happens at service/engine level, or we can add a check constraint.
    # User prompt: "Associate flags with financial year."
    financial_year = Column(String(9), nullable=False)

    # Flag Code (e.g., 'C101' - High Cash Deposit)
    flag_code = Column(String(50), nullable=False)
    
    # Description of the violation
    description = Column(Text, nullable=False)
    
    # Severity (LOW, MEDIUM, HIGH, CRITICAL)
    # Enforced via CHECK constraint (No ENUM)
    severity = Column(String(20), nullable=False)
    
    # Resolution Tracking
    is_resolved = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="compliance_flags")

    __table_args__ = (
        CheckConstraint(
            "severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')",
            name="check_severity_level"
        ),
    )
