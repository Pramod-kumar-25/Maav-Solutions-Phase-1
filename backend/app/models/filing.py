from sqlalchemy import Column, String, ForeignKey, DateTime, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text
from .base import Base

class FilingCase(Base):
    """
    Filing Case Workflow State Machine.
    Tracks the lifecycle of a Tax Return from Draft to Submission.
    """
    __tablename__ = "filing_cases"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    financial_year = Column(String(9), nullable=False)
    
    itr_determination_id = Column(UUID(as_uuid=True), ForeignKey("itr_determinations.id"), nullable=False, index=True)
    
    current_state = Column(String(30), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    submitted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", backref="filing_cases")
    itr_determination = relationship("ITRDetermination")

    __table_args__ = (
        CheckConstraint(
            "current_state IN ('DRAFT', 'READY_FOR_REVIEW', 'LOCKED', 'SUBMITTED')",
            name="check_filing_state_valid"
        ),
        UniqueConstraint('user_id', 'financial_year', name='uq_filing_user_year'),
        UniqueConstraint('itr_determination_id', name='uq_filing_itr_determination'),
    )
