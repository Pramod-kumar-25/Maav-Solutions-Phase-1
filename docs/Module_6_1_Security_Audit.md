# 🛡️ Security Audit Report: Module 6.1 (JWT & Session Phase)

**Date**: 2026-02-21
**Focus**: Authentication Architecture, JWTs, and Session Management

---

## 1. What is Implemented
- **Stateless JWT Generation**: `AuthService.login_user` successfully generates an HS256 JWT containing `sub` (user ID), `primary_role`, and `exp` (expiry).
- **Access Token Expiry**: Hardcoded to 30 minutes in `auth_service.py`.
- **JWT Validation (API Guard)**: `get_current_user` in `deps.py` correctly verifies the JWT signature against `SECRET_KEY`, checks token expiry, ensures the user exists, and checks if the `account_status` is `ACTIVE`.
- **RBAC Foundation**: `RoleChecker` successfully interprets the `primary_role` from the authenticated user object.

## 2. What is Partially Implemented
- **Session Tracking (`auth_sessions` table)**: 
  - **Status**: Write-only.
  - **Details**: When a user logs in, a new record is inserted into `auth_sessions` with 30-minute expiry matching the JWT. However, `get_current_user` **never queries this table**. The security perimeter relies entirely on the stateless JWT.
- **Multiple Device Sessions**: Supported by the database schema (multiple `auth_sessions` per user_id), but completely unmanaged.

## 3. What is Completely Missing
- **Refresh Tokens**: No refresh tokens are generated or accepted. Users are forced to re-authenticate with their password every 30 minutes.
- **Token Revocation / Logout**: There is no `/logout` API route or blacklisting mechanism. A captured token remains fully valid until its 30-minute window expires.
- **Token-to-Session Linking**: The generated JWT lacks a `jti` (Token ID) or `sid` (Session ID) claim, making it impossible to cryptographically link a specific JWT to a specific `auth_sessions` database record.
- **Environment Configuration**: Expiry settings and algorithms are hardcoded constants in `auth_service.py` and `deps.py`, rather than being driven by `config.py`.

---

## 4. Security Gap & Risk Assessment

| Gap / Vulnerability | Risk Level | Impact | Recommended Fix |
| :--- | :--- | :--- | :--- |
| **No Token Revocation** | 🔴 HIGH | If an account is compromised or a user logs out, the access token remains active until expiry. | Link JWTs to DB sessions; validate session status on critical routes and allow revocation. |
| **Silent Session Table** | 🟠 MEDIUM | `auth_sessions` grows indefinitely without providing any security value, misleading developers into thinking sessions are tracked. | Bind JWTs to sessions (`sid` claim) and query session validity for high-risk endpoints. |
| **Missing Refresh Logic** | 🟠 MEDIUM | Severe UX degradation. 30-min access token expiry forces frequent hard logins. | Implement short-lived Access Tokens (15m) and long-lived Refresh Tokens (7d) strictly bound to `auth_sessions`. |
| **Hardcoded Secrets/Config** | 🟡 LOW | Hardcoded `ALGORITHM` and `ACCESS_TOKEN_EXPIRE_MINUTES` reduce environment flexibility. | Move to `core/config.py`. |
| **Weak JWT Payload** | 🟡 LOW | Missing `jti`/`sid` prevents fine-grained token management and device tracking. | Inject `jti` (UUID) and `sid` (Session ID) into JWT payload during login. |

---

## 5. Architectural Recommendation (`auth_sessions` Table)

**Recommendation**: **YES**, heavily utilize the `auth_sessions` table as the foundation for the Refresh Token strategy.

**Proposed Strategy for Module 6.1**:
1. **Access Token (Short-lived, Stateless)**: 15 minutes. Validated rapidly via JWT decoding (no DB lookup for every generic API call). Must carry a `session_id` claim.
2. **Refresh Token (Long-lived, Stateful)**: 7 days. Stored securely and only valid if the corresponding `auth_sessions` record is marked `ACTIVE`.
3. **Session Revocation**: A `/logout` endpoint can mark the `auth_sessions` record as `REVOKED`. The next refresh attempt will fail. Furthermore, critical endpoints (like changing passwords or initiating payments) can optionally perform a real-time check against `auth_sessions` via the `session_id` in the Access Token.
4. **Device Tracking**: By binding the Refresh Token family to the `auth_sessions` table, we gain the ability to list "Active Devices" and allow users to remotely terminate sessions.
