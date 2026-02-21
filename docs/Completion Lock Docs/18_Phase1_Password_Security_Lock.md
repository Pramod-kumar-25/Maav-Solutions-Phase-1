# Module 6.2: Password Security & Account Protection Completion Lock

## 1. Architectural Mandate
Establish a deterministic, race-condition safe password security module with brute-force cooldowns, anti-enumeration tactics, and secure credential rotation logic without unnecessarily changing the existing logical architecture.

## 2. Implementation Boundaries
*   **Target Components**: `user_credentials` table, `AuthService`, `AuthRepository`, `user.py` schemas.
*   **Excluded**: Email-based self-service password reset flows (deferred).

## 3. Verified State
*   **Schema**: Added `last_failed_login_at` (TIMESTAMPTZ) to `user_credentials` to enable state tracking without coupling authentication flow logic to the immutable audit log table.
*   **Password Policies**: Enforced mathematically strictly at the Pydantic tier: 12-char minimum, requiring (a-z, A-Z, 0-9, and symbols) with automatic whitespace sanitization.
*   **Brute-Force & Cooldown**: Locked at 5 attempts and a 15-minute cooldown window.
*   **Concurrency Hardening**: `failed_attempts` increments and resets are bound within `async with session.begin()` transactions querying specific rows with `.with_for_update()` to enforce row-level locking. This prevents "lost updates" during parallel login barrages.
*   **Anti-Enumeration**: Both "User Not Found" and "Active Cooldown" scenarios simulate realistic backend latency using a pre-calculated dummy bcrypt hash to deter timing-based enumeration attacks. Both return an identical static HTTP 401 response payload.
*   **Credential Rotation**: `change_password` enforces strict validation, ensures active session authentication, and executes securely by instantly revoking all active concurrent sessions tied to the user (excluding the active session performing the change).

## 4. Deviation Log
*   **Constraint Lifted**: Added `last_failed_login_at` to the schema. A minor addition was required because enforcing cooldown periods by querying arbitrary timestamps from massive `audit_logs` collections during high-velocity login bursts introduced non-deterministic latency and violated separation of concerns.

## 5. Artifacts Locked
*   `backend/alembic/versions/b7d21390483c_add_last_failed_login_at.py`
*   `backend/app/models/user.py` (`UserCredentials` updates)
*   `backend/app/schemas/user.py` (Strict Password Types)
*   `backend/app/repositories/auth_repository.py` (For-Update locking logic)
*   `backend/app/services/auth_service.py` (Brute-force and Rotation implementation)

## 6. Zero-Regression Confirmation
*   [x] Password strength enforced at validation tier.
*   [x] Deterministic 15-minute temporary lockout after 5 failed attempts.
*   [x] Atomic failed attempt increments using row-level locking.
*   [x] No reliance on audit logs for cooldown logic.
*   [x] Anti-enumeration protections in place.
*   [x] Password change revokes all other active sessions.
