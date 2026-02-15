from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, DateTime, Text, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text
from .base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    pan = Column(String(10), unique=True, nullable=False)
    legal_name = Column(Text, nullable=False)
    email = Column(Text, unique=True, nullable=False)
    mobile = Column(String(15), nullable=False)
    primary_role = Column(String(20), nullable=False)  # Check constraint handled in DB
    account_status = Column(String(20), nullable=False, server_default=text("'ACTIVE'"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    credentials = relationship("UserCredentials", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("AuthSession", back_populates="user", cascade="all, delete-orphan")
    taxpayer_profile = relationship("TaxpayerProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    business_profile = relationship("BusinessProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    compliance_flags = relationship("ComplianceFlag", back_populates="user", cascade="all, delete-orphan")
    itr_determinations = relationship("ITRDetermination", back_populates="user", cascade="all, delete-orphan")

class UserCredentials(Base):
    __tablename__ = "user_credentials"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    auth_provider = Column(String(30), nullable=False)
    password_hash = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, server_default=text("true"))
    failed_attempts = Column(Integer, nullable=False, server_default=text("0"))
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Constraints from DB
    __table_args__ = (
        UniqueConstraint('user_id', 'auth_provider', name='unique_user_provider'),
        CheckConstraint("auth_provider IN ('PASSWORD')", name='check_auth_provider'),
    )

    # Relationship
    user = relationship("User", back_populates="credentials")

class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    auth_method = Column(String(20), nullable=False)
    device_id = Column(Text, nullable=True)
    ip_address = Column(INET, nullable=True)
    session_start = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    session_expiry = Column(DateTime(timezone=True), nullable=False)

    # Relationship
    user = relationship("User", back_populates="sessions")
