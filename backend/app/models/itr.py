from sqlalchemy import Column, String, Boolean, ForeignKey, Text, CheckConstraint, UniqueConstraint, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base

class ITRDetermination(Base):
    """
    ITR Determination Enity.
    Stores the determined ITR form type for a user and financial year.
    """
    __tablename__ = "itr_determinations"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    financial_year = Column(String(9), nullable=False)
    itr_type = Column(String(20), nullable=False)
    reason = Column(Text, nullable=False)
    
    is_locked = Column(Boolean, default=False, nullable=False)
    determined_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="itr_determinations")

    __table_args__ = (
        CheckConstraint(
            "itr_type IN ('ITR-1', 'ITR-2', 'ITR-3')",
            name="check_itr_type_valid"
        ),
        UniqueConstraint('user_id', 'financial_year', name='uq_itr_user_financial_year'),
    )
