# 🔐 Completion Lock: Module 5.11 – CA Assignment & Consent Workflow

**Status**: LOCKED 🔒
**Date**: 2026-02-15
**Version**: 1.0

---

## 1. Scope Summary
This module implements the **Consent Architecture** (inspired by DPDP Act principles) and the **Chartered Accountant (CA) Assignment** workflow. It enforces a strict "Consent First" policy where no CA can access a Taxpayer's data without an active, granular, and revocable `ConsentArtifact`.

## 2. Implemented Components

### A. Data Layer (Models)
- **`ConsentArtifact`**: Represents a specific grant of permission (Purpose, Scope, Expiry) from a User to a CA.
- **`CAAssignment`**: Represents the operational link between a CA and a specific Filing Case, contingent on a valid Consent.
- **`ConsentAuditLog`**: Immutable record of all lifecycle events (GRANT, REVOKE, EXPIRE).

### B. Repository Layer
- **`ConsentRepository`**: Handles lifecycle of Consents.
- **`CAAssignmentRepository`**: Handles lifecycle of Assignments.
- **`ConsentAuditRepository`**: Write-only access for audit trails.

### C. Service Layer
- **`ConsentService`**: Managing granting/revocation logic.
- **`CAAssignmentService`**: Validates cross-module rules (Taxpayer existence, Filing existence) and enforces assignments.

### D. API Layer
- **`consent.py`**: Router exposing:
    - `POST /consent/`: Grant consent.
    - `POST /consent/{id}/revoke`: Revoke consent.
    - `POST /consent/assignments`: Assign CA to Filing.
- **Security**: Validates `INDIVIDUAL` or `BUSINESS` roles.

### E. Dependencies
- **`require_valid_ca_assignment`**: A critical dependency that acts as a runtime gatekeeper. It checks:
    1. Caller is a CA.
    2. Assignment exists and is ACTIVE.
    3. Underlying Consent exists, is ACTIVE, and NOT EXPIRED.

## 3. Architectural Guarantees

### A. "Code is Law"
- **Schema Alignment**: ORM models map strictly to `consent_artifacts`, `ca_assignments`, and `consent_audit_logs` tables.
- **State Management**: Statuses (`ACTIVE`, `REVOKED`, `EXPIRED`) are enforced by the Service layer / Database state, not ad-hoc logic.

### B. Compliance (DPDP Alignment)
- **Granularity**: Consent is not global; it is scoped (e.g., "VIEW_FINANCIALS", "FILE_RETURNS").
- **Revocability**: Users can revoke consent at any time, immediately invalidating access.
- **Auditability**: Every action is logged in `consent_audit_logs`.

### C. Transaction Discipline
- **Atomicity**: Critical operations (Granting, Assigning) are wrapped in `async with session.begin()` within the API layer to ensure data integrity.

### D. Exception Handling
- **Typed Exceptions**: Replaced generic errors with `NotFoundError`, `UnauthorizedError`, `ValidationError`.
- **Deterministic Mapping**: API layer maps these strictly to 404, 403, and 400.

## 4. Verification
- **Manual Testing**: API endpoints verified for success and failure scenarios.
- **Code Review**: No "fallback" or "catch-all" error handlers in the final build.
