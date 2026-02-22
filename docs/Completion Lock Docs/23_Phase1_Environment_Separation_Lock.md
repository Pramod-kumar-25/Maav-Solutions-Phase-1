# Module 6.7: Production Environment Separation Complete Lock

## 1. Architectural Mandate
Establish a mathematically opaque boundary between local development and deployed infrastructure. The deployed application must actively defend against reconnaissance by disabling architectural schemas, choking verbosity, and masking topology responses from unauthenticated pings, while `APP_ENV` strictly dictates this bifurcation.

## 2. Implementation Boundaries
*   **Target Components**: `app/core/config.py`, `app/main.py`.
*   **Excluded**: Modifying auth mechanics, disabling rate limiters, or tampering with actual health resolution checks.

## 3. Verified State
*   **Explicit Environment Typing**: `APP_ENV` is statically typed as `Literal["development", "staging", "production"]`. Unrecognized strings or omitted keys aggressively crash the server via explicit Pydantic TypeErrors on startup, stopping silent `"development"` default escalations in staging clusters.
*   **Logging Strictness**: The `Settings.validate_production_secrets` method intercepts `APP_ENV` states. If evaluated to `staging` or `production`, any `LOG_LEVEL="DEBUG"` injection dynamically crashes the system, guaranteeing high-verbosity network dumps or query payloads are never shipped to log aggregators in live environments.
*   **Swagger Disablement**: App instantiation in `main.py` evaluates `APP_ENV`. All documentation schema endpoints (`openapi_url`, `docs_url`, `redoc_url`) default to `None` permanently when deployed, completely blinding the API topology to exterior scraping without altering any internal Pydantic definitions.
*   **Health Obfuscation**: The database connection ping is intact. A success yields `{"status": "ok"}`. A failure yields `503 Service Unavailable`. Development-exclusive footprints (like printing exception errors back) are explicitly stripped when deployed.

## 4. Artifacts Locked
*   `backend/app/core/config.py` (Literal mapping and Log strictness)
*   `backend/app/main.py` (App configuration kwargs and Health checks)

## 5. Zero-Regression Confirmation
*   [x] `APP_ENV` is restricted to `Literal["development", "staging", "production"]`.
*   [x] Application fails startup if `APP_ENV` is invalid.
*   [x] Swagger, Redoc, and OpenAPI JSON are disabled in staging and production.
*   [x] `LOG_LEVEL="DEBUG"` is rejected in staging and production.
*   [x] Health endpoint does not leak infrastructure details in staging and production.
*   [x] No development conveniences are available outside development.
*   [x] No regression occurred in secrets validation or CORS enforcement.
