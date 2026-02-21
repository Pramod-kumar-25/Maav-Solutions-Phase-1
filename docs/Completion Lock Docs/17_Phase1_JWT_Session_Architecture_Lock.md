# Module 6.1: JWT & Session Architecture Completion Lock

## 1. Architectural Mandate
Establish a secure, production-grade JWT and refresh token architecture for Phase 1. This must include short-lived stateless access tokens, stateful cryptographically hashed refresh tokens, strict replay detection, atomic transactions, and environment-driven configuration hardening.

## 2. Implementation Boundaries
*   **Target Components**: `auth_sessions` table, `AuthService`, `AuthRepository`, `deps.py`, `config.py`.
*   **Excluded**: Multi-device generic session management UI, exhaustive OAuth2 provider integration.

## 3. Verified State
*   **Schema**: `auth_sessions` expanded to include `refresh_token_hash` and `status` via Alembic migration (`alembic revision`).
*   **Access Tokens**: 15-minute expiry, include `sid` and `jti` claims.
*   **Refresh Tokens**:
    *   7-day expiry, opaque random 64-byte hex strings.
    *   Hashed with SHA-256 for at-rest security.
    *   Full payload format: `{session_id}:{raw_token}` to avoid database scans and ensure O(1) lookups.
*   **Replay Detection**: Single-use refresh tokens. On rotation, if the provided token hash doesn't match the active hash in the database, the session is instantly `REVOKED` inside an atomic transaction, neutralizing compromised tokens.
*   **Transaction Safety**: Entire refresh and login flows wrap database updates and validations within an `async with session.begin():` block.
*   **Secrets**: `JWT_SECRET_KEY` config hardened with strict Pydantic validation; will crash on startup in `production` if using the fallback key.
*   **RBAC & Security**: Added `require_active_session` dependency for high-security endpoints requiring database-backed session validation. All authentication business logic strictly throws typed exceptions (`UnauthorizedError`, `NotFoundError`, etc.).

## 4. Deviation Log
*   **Constraint Lifted**: The initial aim was to avoid schema changes. However, properly securing refresh tokens required adding `refresh_token_hash` and `status` to `auth_sessions`. An Alembic migration was necessary to ensure cryptographic security.

## 5. Artifacts Locked
*   `db/schema.sql` (auth_sessions table)
*   `backend/app/models/user.py` (AuthSession)
*   `backend/app/schemas/token.py` (Token extensions)
*   `backend/app/core/config.py` (Auth Configurations)
*   `backend/app/repositories/auth_repository.py`
*   `backend/app/services/auth_service.py`
*   `backend/app/api/deps.py`
*   `backend/app/api/auth.py`

## 6. Zero-Regression Confirmation
*   [x] Replay detection tested logic.
*   [x] Fallback secret blocked in production.
*   [x] Typed exceptions used universally in AuthService.
*   [x] Access token stateless validation preserved via `sid` extraction.
*   [x] Refresh and logout endpoints implemented and atomic.
