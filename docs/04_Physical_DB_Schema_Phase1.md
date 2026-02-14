# Physical DB Schema (Phase-1)

This document describes the physical implementation of the Logical Data Model in PostgreSQL.
**Authoritative Source**: `db/schema.sql`

## 1. Core Tables

### 1.1 `users`
- **Primary Key**: `id` (UUIDv4)
- **Constraints**:
    - `pan` UNIQUE, 10 chars.
    - `email` UNIQUE.
    - `primary_role` IN ('INDIVIDUAL', 'BUSINESS', 'CA', 'ADMIN').
    - `account_status` DEFAULT 'ACTIVE'.

### 1.2 `auth_sessions`
- **Foreign Key**: `user_id` -> `users(id)` (ON DELETE CASCADE).
- **Purpose**: Tracks active sessions.
- **Index**: `idx_auth_user` on `user_id`.

## 2. Taxpayer Data

### 2.1 `taxpayer_profiles`
- **Foreign Key**: `user_id` -> `users(id)` (ON DELETE CASCADE, UNIQUE).
- **Constraints**:
    - `pan_type` CHAR(1).
    - `residential_status` IN ('RESIDENT', 'RNOR', 'NRI').
    - `aadhaar_link_status` DEFAULT false.

### 2.2 `business_entities`
- **Foreign Key**: `owner_user_id` -> `users(id)` (ON DELETE CASCADE).
- **Constraints**: `gstin` UNIQUE (Nullable).
- **Index**: `idx_business_owner` on `owner_user_id`.

### 2.3 `income_records`
- **Foreign Key**: `taxpayer_id` -> `taxpayer_profiles(id)` (ON DELETE CASCADE).
- **Foreign Key**: `source_id` -> `data_sources(id)` (Nullable).
- **Check**: `amount >= 0`.
- **Index**: `idx_income_taxpayer`, `idx_income_source`.

### 2.4 `expense_records`
- **Foreign Key**: `business_id` -> `business_entities(id)` (ON DELETE CASCADE).
- **Check**: `amount >= 0`.
- **Index**: `idx_expense_business`.

## 3. Compliance & Filing

### 3.1 `compliance_flags`
- **Foreign Key**: `taxpayer_id` -> `taxpayer_profiles(id)` (ON DELETE CASCADE).
- **Constraints**: `severity` IN ('HARD', 'SOFT').
- **Index**: `idx_compliance_taxpayer`.

### 3.2 `filing_cases`
- **Foreign Key**: `taxpayer_id` -> `taxpayer_profiles(id)` (ON DELETE CASCADE).
- **Constraints**: `filing_mode` IN ('SELF', 'CA').
- **Index**: `idx_filing_taxpayer`.

### 3.3 `user_confirmations`
- **Foreign Key**: `filing_id` -> `filing_cases(id)` (ON DELETE CASCADE).
- **Foreign Key**: `confirmed_by` -> `users(id)`.
- **Index**: `idx_user_confirm_filing`, `idx_user_confirm_user`.

## 4. Audit & Security

### 4.1 `consent_artifacts`
- **Foreign Key**: `user_id` -> `users(id)` (ON DELETE CASCADE).
- **Status**: ACTIVE, REVOKED, EXPIRED.
- **Index**: `idx_consent_user`.

### 4.2 `audit_logs`
- **Foreign Key**: `actor_id` -> `users(id)` **(ON DELETE SET NULL)**.
- **Reason**: We must retain audit history even if the user is deleted.
- **Content**: `action`, `before_value` (JSONB), `after_value` (JSONB).
- **Index**: `idx_audit_actor`.

## 5. Extensions
- `uuid-ossp`: For UUID generation.
- `pgcrypto`: For potential hashing/encryption needs.
