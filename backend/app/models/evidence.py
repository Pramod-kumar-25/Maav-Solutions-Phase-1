from sqlalchemy import Column, String, Text, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import text
from .base import Base

class EvidenceRecord(Base):
    """
    Evidence Record Model.
    Maps strictly to 'evidence_records' table.
    Stores metadata for cryptographically verifiable artifacts.
    """
    __tablename__ = "evidence_records"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    
    # URN format: urn:entity:id:action
    related_action = Column(Text, nullable=True)
    
    # SHA-256 Hash of the canonical payload
    hash = Column(Text, nullable=False)
    
    # Relative path to blob storage
    storage_location = Column(Text, nullable=False)
    
    # Date when the evidence can be purged (policy driven)
    retention_expiry = Column(Date, nullable=True)
