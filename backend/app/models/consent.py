from typing import Optional
from datetime import datetime
from sqlalchemy import ForeignKey, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func, text
from .base import Base

class ConsentArtifact(Base):
    """
    Consent Artifact Model.
    Tracks granular user consent for data access/actions.
    Aligned with 'consent_artifacts' table.
    """
    __tablename__ = "consent_artifacts"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    purpose: Mapped[str] = mapped_column(String(50), nullable=False)
    scope: Mapped[str] = mapped_column(Text, nullable=False)
    consent_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expiry_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Relationships
    user = relationship("User", backref="consents")
    audit_logs = relationship("ConsentAuditLog", back_populates="consent")
    ca_assignments = relationship("CAAssignment", back_populates="consent")

class CAAssignment(Base):
    """
    CA Assignment Model.
    Links a Filing Case + User (CA) + Consent.
    Aligned with 'ca_assignments' table.
    """
    __tablename__ = "ca_assignments"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    filing_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("filing_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    ca_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    consent_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("consent_artifacts.id"), nullable=False, index=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Relationships
    filing_case = relationship("FilingCase", backref="ca_assignments")
    ca_user = relationship("User", foreign_keys=[ca_user_id], backref="assigned_filings")
    consent = relationship("ConsentArtifact", back_populates="ca_assignments")

class ConsentAuditLog(Base):
    """
    Consent Audit Log Model.
    Tracks lifecyle events of a Consent Artifact.
    Aligned with 'consent_audit_logs' table.
    """
    __tablename__ = "consent_audit_logs"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    consent_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("consent_artifacts.id", ondelete="CASCADE"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    actor_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    consent = relationship("ConsentArtifact", back_populates="audit_logs")
    actor = relationship("User")
