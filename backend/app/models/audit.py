from sqlalchemy import Column, String, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.sql import func, text
from .base import Base

class AuditLog(Base):
    """
    Audit Log Model.
    Aligned to existing schema.
    """
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    actor_role = Column(String(20), nullable=True)
    
    action = Column(Text, nullable=False)
    
    before_value = Column(JSONB, nullable=True)
    after_value = Column(JSONB, nullable=True)
    
    ip_address = Column(INET, nullable=True)
    device_id = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
