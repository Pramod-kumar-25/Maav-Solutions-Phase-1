-- =====================================================
-- MAAV Phase-1 Non-AI Physical Schema
-- Authoritative Source of Truth
-- =====================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =====================================================
-- USERS
-- =====================================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pan VARCHAR(10) UNIQUE NOT NULL CHECK (length(pan) = 10),
    legal_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    mobile VARCHAR(15) NOT NULL,
    primary_role VARCHAR(20) NOT NULL CHECK (
        primary_role IN ('INDIVIDUAL','BUSINESS','CA','ADMIN')
    ),
    account_status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =====================================================
-- AUTH SESSIONS
-- =====================================================

CREATE TABLE auth_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    auth_method VARCHAR(20) NOT NULL,
    device_id TEXT,
    ip_address INET,
    session_start TIMESTAMPTZ NOT NULL DEFAULT now(),
    session_expiry TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_auth_user ON auth_sessions(user_id);

-- =====================================================
-- CONSENT
-- =====================================================

CREATE TABLE consent_artifacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    purpose VARCHAR(50) NOT NULL,
    scope TEXT NOT NULL,
    consent_version VARCHAR(20),
    granted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expiry_at TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (
        status IN ('ACTIVE','REVOKED','EXPIRED')
    )
);

CREATE INDEX idx_consent_user ON consent_artifacts(user_id);

CREATE TABLE consent_audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    consent_id UUID NOT NULL REFERENCES consent_artifacts(id) ON DELETE CASCADE,
    action VARCHAR(20) NOT NULL,
    actor_id UUID REFERENCES users(id) ON DELETE SET NULL,
    reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_consent_audit_consent ON consent_audit_logs(consent_id);
CREATE INDEX idx_consent_audit_actor ON consent_audit_logs(actor_id);

-- =====================================================
-- TAXPAYER PROFILE
-- =====================================================

CREATE TABLE taxpayer_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    pan_type CHAR(1) NOT NULL,
    residential_status VARCHAR(20) CHECK (
        residential_status IN ('RESIDENT','RNOR','NRI')
    ),
    default_tax_regime VARCHAR(20) NOT NULL DEFAULT 'NEW',
    aadhaar_link_status BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =====================================================
-- BUSINESS ENTITY
-- =====================================================

CREATE TABLE business_entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    entity_type VARCHAR(30) NOT NULL,
    gstin VARCHAR(15) UNIQUE,
    msme_status BOOLEAN NOT NULL DEFAULT false,
    incorporation_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_business_owner ON business_entities(owner_user_id);

-- =====================================================
-- DATA SOURCES
-- =====================================================

CREATE TABLE data_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_type VARCHAR(30) NOT NULL CHECK (
        source_type IN ('AIS','AA','UPLOAD')
    ),
    reference_number TEXT,
    retrieved_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =====================================================
-- INCOME
-- =====================================================

CREATE TABLE income_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    taxpayer_id UUID NOT NULL REFERENCES taxpayer_profiles(id) ON DELETE CASCADE,
    income_head VARCHAR(50) NOT NULL,
    amount NUMERIC(15,2) NOT NULL CHECK (amount >= 0),
    financial_year VARCHAR(9) NOT NULL,
    source_id UUID REFERENCES data_sources(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_income_taxpayer ON income_records(taxpayer_id);
CREATE INDEX idx_income_source ON income_records(source_id);

-- =====================================================
-- EXPENSES
-- =====================================================

CREATE TABLE expense_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id UUID NOT NULL REFERENCES business_entities(id) ON DELETE CASCADE,
    category VARCHAR(50),
    amount NUMERIC(15,2) NOT NULL CHECK (amount >= 0),
    payment_mode VARCHAR(20),
    invoice_date DATE,
    msme_flag BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_expense_business ON expense_records(business_id);

-- =====================================================
-- COMPLIANCE
-- =====================================================

CREATE TABLE compliance_flags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    taxpayer_id UUID NOT NULL REFERENCES taxpayer_profiles(id) ON DELETE CASCADE,
    rule_code VARCHAR(50) NOT NULL,
    severity VARCHAR(10) NOT NULL CHECK (
        severity IN ('HARD','SOFT')
    ),
    triggered_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    status VARCHAR(20) NOT NULL DEFAULT 'OPEN'
);

CREATE INDEX idx_compliance_taxpayer ON compliance_flags(taxpayer_id);

-- =====================================================
-- ITR DETERMINATION
-- =====================================================

CREATE TABLE itr_determinations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    taxpayer_id UUID NOT NULL REFERENCES taxpayer_profiles(id) ON DELETE CASCADE,
    financial_year VARCHAR(9) NOT NULL,
    itr_type VARCHAR(10) NOT NULL,
    locked_by VARCHAR(20),
    lock_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_itr_taxpayer ON itr_determinations(taxpayer_id);

-- =====================================================
-- FILING
-- =====================================================

CREATE TABLE filing_cases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    taxpayer_id UUID NOT NULL REFERENCES taxpayer_profiles(id) ON DELETE CASCADE,
    financial_year VARCHAR(9) NOT NULL,
    filing_mode VARCHAR(20) NOT NULL CHECK (
        filing_mode IN ('SELF','CA')
    ),
    current_state VARCHAR(30) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_filing_taxpayer ON filing_cases(taxpayer_id);

CREATE TABLE submission_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filing_id UUID NOT NULL REFERENCES filing_cases(id) ON DELETE CASCADE,
    attempt_no INT NOT NULL,
    ack_number TEXT,
    submitted_at TIMESTAMPTZ,
    status VARCHAR(20)
);

CREATE INDEX idx_submission_filing ON submission_records(filing_id);

CREATE TABLE user_confirmations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filing_id UUID NOT NULL REFERENCES filing_cases(id) ON DELETE CASCADE,
    confirmation_type VARCHAR(50) NOT NULL,
    confirmed_by UUID NOT NULL REFERENCES users(id),
    ip_address INET,
    confirmed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_user_confirm_filing ON user_confirmations(filing_id);
CREATE INDEX idx_user_confirm_user ON user_confirmations(confirmed_by);

CREATE TABLE ca_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filing_id UUID NOT NULL REFERENCES filing_cases(id) ON DELETE CASCADE,
    ca_user_id UUID NOT NULL REFERENCES users(id),
    consent_id UUID NOT NULL REFERENCES consent_artifacts(id),
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    status VARCHAR(20)
);

CREATE INDEX idx_ca_assign_filing ON ca_assignments(filing_id);
CREATE INDEX idx_ca_assign_user ON ca_assignments(ca_user_id);
CREATE INDEX idx_ca_assign_consent ON ca_assignments(consent_id);

-- =====================================================
-- AUDIT (IMMUTABLE)
-- =====================================================

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    actor_id UUID REFERENCES users(id) ON DELETE SET NULL,
    actor_role VARCHAR(20),
    action TEXT NOT NULL,
    before_value JSONB,
    after_value JSONB,
    ip_address INET,
    device_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_audit_actor ON audit_logs(actor_id);

-- =====================================================
-- EVIDENCE
-- =====================================================

CREATE TABLE evidence_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    related_action TEXT,
    hash TEXT NOT NULL,
    storage_location TEXT NOT NULL,
    retention_expiry DATE
);
