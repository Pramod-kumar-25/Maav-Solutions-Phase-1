from sqlalchemy import Column, String, Numeric, ForeignKey, DateTime, Date, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text
from .base import Base

class FinancialEntry(Base):
    """
    Unified Ledger Entry.
    Stores both Income and Expense records for INDIVIDUAL and BUSINESS users.
    """
    __tablename__ = "financial_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Core Financial Data
    entry_type = Column(String(10), nullable=False) # INCOME / EXPENSE
    category = Column(String(100), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    
    # Period & Timing
    financial_year = Column(String(9), nullable=False) # e.g., "2024-25"
    entry_date = Column(Date, nullable=False)
    
    # Metadata
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("entry_type IN ('INCOME', 'EXPENSE')", name='check_entry_type'),
        CheckConstraint("amount >= 0", name='check_amount_positive'),
    )

    # Relationships
    user = relationship("User", backref="financial_entries")
