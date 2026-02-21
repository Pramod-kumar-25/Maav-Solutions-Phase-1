# Module 6.4: Centralized Exception Handling Standardization Complete Lock

## 1. Architectural Mandate
Establish a global, centralized exception handling boundary that provides a unified, predictable JSON envelope for all API errors, ensuring that internal state and stack traces are never leaked to the client while preserving full observability for internal debugging.

## 2. Implementation Boundaries
*   **Target Components**: `app/core/exception_handlers.py` (New), `app/main.py`, All API Routers (`app/api/*.py`), `app/services/*.py`.
*   **Excluded**: Modifying business logic or specific authentication/rate-limiting requirements.

## 3. Verified State
*   **Unified Error Envelope**: All API errors are strictly serialized into a `{"error": {"code", "message", "timestamp", "path"}}` format. No double-wrapping occurs.
*   **Deterministic Code Mapping**: Uses `HTTP_STATUS_TO_CODE_MAP` to translate HTTP statuses (e.g., 400 to `BAD_REQUEST`, 429 to `RATE_LIMITED`) deterministically without dynamic guesswork.
*   **Preservation of Detail**: `HTTPException.detail` is accurately preserved and injected into the envelope's `message` field.
*   **Timestamp & Path**: Timestamps use strictly UTC ISO 8601 formatting. Paths are securely derived from `request.url.path`.
*   **Service Purity**: The Service Layer relies exclusively on domain exceptions (`ValidationError`, `NotFoundError`, `UnauthorizedError`) and remains HTTP-agnostic.
*   **Router Cleanliness**: Redundant `try...except` HTTP translation boundaries have been purged from all controllers.
*   **Logging Observability & Security**: 
    *   4xx errors are logged at the `INFO` level to prevent log pollution.
    *   5xx generic errors (`Exception`) are logged at the `ERROR` level, securely capturing the full `sys.exc_info()` stack trace on the backend while presenting a generic 500 blindly to the client.

## 4. Artifacts Locked
*   `backend/app/core/exception_handlers.py`
*   `backend/app/main.py`
*   API Router Layer (`backend/app/api/*.py`)
*   Service Layer domain exception references.

## 5. Zero-Regression Confirmation
*   [x] Unified error envelope across all API errors.
*   [x] Deterministic mapping from HTTP status codes to machine-readable error codes.
*   [x] Preservation of `HTTPException.detail` as the message field.
*   [x] Explicit mapping of 429 to `RATE_LIMITED`.
*   [x] No double-wrapping of error envelopes.
*   [x] UTC ISO 8601 timestamp generation.
*   [x] Path derived strictly from `request.url.path`.
*   [x] Domain services remain HTTP-agnostic.
*   [x] Routers contain no redundant exception translation.
*   [x] 4xx errors logged at INFO level.
*   [x] 5xx errors logged at ERROR level with stack traces internally.
*   [x] No stack traces leak to client responses.
