# Security & Audit Principles: Phase-1

## 1. Role-Based Access Control (RBAC)

Access is strictly controlled based on user roles:
- **Individual**: Can only access their own data.
- **Business**: Can manage business entities and related income/expenses.
- **CA (Chartered Accountant)**: Can access **Consented** data of other valid users.
- **Admin**: System-wide access (Phase-1 limited scope, mostly logging/dev).

## 2. Consent-First Architecture

Phase-1 implements a **Granular Consent Model**:
- **Explicit Grant**: Users must explicitly grant access to their data via the `/api/v1/consent` endpoint.
- **Scope Definition**: Consent is scoped (e.g., "Access Income Records for FY 2023-24").
- **Revocation**: Users can revoke consent at any time (`POST /consent/{id}/revoke`).
- **Audit Trail**: All consent actions (Grant, Revoke, Expire) are logged immutably.

## 3. Immutable Audit Logging

Every critical data mutation or access is logged to the `audit_logs` table.
- **Immutability**: The `audit_logs` table is designed to be append-only. No updates or deletes allowed (application level enforcement).
- **Comprehensive Context**: Each log entry captures:
    - **Actor**: `actor_id` (Who performed the action).
    - **Action**: `action` (What happened - e.g., "Filing Submission").
    - **State Change**: `before_value` and `after_value` (If applicable).
    - **Context**: `ip_address`, `device_id` (From request headers).
- **Resilience**: `ON DELETE SET NULL` on `actor_id` ensures logs remain even if a user is deleted.

## 4. Human Confirmation

MaaV Phase-1 enforces "Human-in-the-Loop" for high-stakes actions:
- **Tax Calculation Finalization**: User must review and confirm the computed tax liability.
- **Filing Submission**: User must authorize the final submission (simulating Digital Signature/OTP confirmation).
- **Legal Compliance**: This ensures user intent is captured and stored (`user_confirmations` table).

## 5. Security Measures

- **Authentication**: JWT (Stateless) with `pydantic` validation.
- **Password Hashing**: `bcrypt` (via `passlib`).
- **HTTPS**: Enforced at the gateway level.
- **Input Validation**: Strict Pydantic models for all API endpoints to prevent injection attacks.
- **CSRF**: Protection active for state-changing requests (via middleware).
