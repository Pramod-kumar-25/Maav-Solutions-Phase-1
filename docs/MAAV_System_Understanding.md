# MaaV Solutions Phase-1: System Understanding Document

## 1. SYSTEM OVERVIEW
**What the application does:**
MaaV Solutions is an automated tax filing orchestration engine and compliance platform. The Phase-1 backend is designed to securely onboard users, establish their taxpayer profiles, aggregate their financial entries (Income/Expense), and orchestrate the lifecycle of their tax filings through a strictly controlled state machine.

**Core purpose:**
To enforce deterministic, failure-safe business logic for tax case preparation before submission to authorities, ensuring mathematical accuracy, state integrity, and absolute data isolation.

**Main domains:**
1. **Auth**: Secure user onboarding and JWT-based session management.
2. **Taxpayer**: Establishing the financial identity, residency status, and default tax configurations for a user.
3. **Filing**: Managing the core tax case lifecycle via a strictly enforced progression state machine.
4. **Financial**: Aggregating granular income and expense records mapped directly to an active filing.

---

## 2. ARCHITECTURE
**High-level architecture (API → Service → Repository → DB):**
The application adheres to a strict layered architecture pattern leveraging FastAPI, SQLAlchemy (Async), and PostgreSQL.

*   **API Layer (`routers`)**: Handles HTTP ingress, payload schema validation (Pydantic), and Authentication dependency injection. It delegates all business logic to the Service Layer.
*   **Service Layer (`services`)**: The "brain" of the application. Enforces business rules, state machine transitions, and data validation. It orchestrates logic completely independently of HTTP context or database dialect.
*   **Repository Layer (`repositories`)**: The data access layer. Maps domain operations to pure SQLAlchemy async queries, abstracting the database away from the service logic.
*   **Data Layer (`models`)**: SQLAlchemy ORM models defining the exact PostgreSQL table structures.

**How requests flow through the system:**
1. Client sends HTTP request → 2. FastAPI matches Router → 3. Pydantic validates Schema → 4. Dependency Injection extracts User Token & DB Session → 5. Router calls Service → 6. Service enforces Business Rules → 7. Service calls Repository → 8. Repository executes SQL → 9. Data cascades back up as an HTTP Response.

---

## 3. MODULE BREAKDOWN

### A) Auth Module
*   **Responsibilities**: Securely managing user identities and emitting authentication tokens.
*   **Key operations**: Registration (Duplicate prevention), Login (Password hashing verification).
*   **Business rules**: Passwords are cryptographically hashed using `passlib` (bcrypt). Duplicate email registrations are strictly blocked with 400/409 HTTP exceptions.

### B) Taxpayer Module
*   **Responsibilities**: Capturing the user's fiscal profile and tax residency logic.
*   **Key operations**: Profile creation, profile retrieval.
*   **Business rules**: A User may only have exactly ONE Taxpayer Profile (1:1 constraint). Schema strictly enforces data typings (e.g., `days_in_india_current_fy` for residency calculations).

### C) Filing Module
*   **Responsibilities**: Orchestrating the preparation lifecycle of a tax case.
*   **Key operations**: Initialization of a case, sequential state mutation.
*   **Business rules**: Filings must obey a strictly directional State Machine. Invalid transitions (e.g., skipping from creation directly to verification) trigger domain-level exceptions mapping to HTTP 400 errors.

### D) Financial Module
*   **Responsibilities**: Aggregation of individual ledger records bound to a filing.
*   **Key operations**: Creating `INCOME` entries, creating `EXPENSE` entries, fetching entry aggregations.
*   **Business rules**: Amounts must be positive (>= 0). Entry types are strictly confined to predefined enums. All entries must explicitly link to an existing, valid Filing ID.

---

## 4. DATA MODELS
*   **User**: 
    *   *Key Fields*: `id`, `email`, `hashed_password`, `primary_role`.
    *   *Relationships*: 1:1 with `TaxpayerProfile`.
*   **TaxpayerProfile**: 
    *   *Key Fields*: `id`, `user_id`, `days_in_india_current_fy`, `default_tax_regime`.
    *   *Relationships*: Belongs to `User` (FK: `user_id`).
*   **FilingCase (Filing)**: 
    *   *Key Fields*: `id`, `taxpayer_id`, `financial_year`, `status`.
    *   *Relationships*: Belongs to `TaxpayerProfile` (FK: `taxpayer_id`). 1:Many with `FinancialEntry`.
*   **FinancialEntry**: 
    *   *Key Fields*: `id`, `filing_id`, `type` (INCOME/EXPENSE), `amount`, `description`.
    *   *Relationships*: Belongs to `FilingCase` (FK: `filing_id`).

---

## 5. API ENDPOINTS

### Auth Module
*   `POST` `/api/v1/auth/register` — Register a new user. *(Auth Required: No)*
*   `POST` `/api/v1/auth/login` — Exchange credentials for JWT access token. *(Auth Required: No)*

### Taxpayer Module
*   `POST` `/api/v1/taxpayer/profile` — Create taxpayer profile for active user. *(Auth Required: Yes)*
*   `GET` `/api/v1/taxpayer/profile` — Fetch taxpayer profile for active user. *(Auth Required: Yes)*

### Filing Module
*   `POST` `/api/v1/filings` — Initialize a new filing draft. *(Auth Required: Yes)*
*   `PATCH` `/api/v1/filings/{id}` — Progress filing state machine. *(Auth Required: Yes)*

### Financial Module
*   `POST` `/api/v1/financial-entries` — Add income/expense record to a filing. *(Auth Required: Yes)*
*   `GET` `/api/v1/financial-entries?filing_id={id}` — Fetch all records for a given filing. *(Auth Required: Yes)*

---

## 6. BUSINESS LOGIC RULES
*   **PAN Validation Logic**: Constrained by strict regex formatting within Pydantic schemas enforcing Indian Government PAN structuring.
*   **Taxpayer Constraints**: Profile duplication is inherently blocked by database unique constraints and service-layer gating.
*   **Filing State Machine Rules**: Enforces pure sequential progression. Any attempts to bypass logic checks are denied at the Service Layer.
*   **Financial Validation Rules**: Negative amounts are rejected. Unknown enums ("REFUND", "DEDUCTION" etc., if not modeled yet) are dropped by Pydantic validation before ever touching the database.

---

## 7. USER FLOW 
1.  **Register**: The user submits their email and password to `/api/v1/auth/register`. The system hashes the password and creates a `User` record.
2.  **Login**: The user submits credentials to `/api/v1/auth/login`. The system validates the hash and returns a JWT `access_token`.
3.  **Create taxpayer profile**: The user attaches the JWT as a `Bearer` token and submits residency logic to `POST /api/v1/taxpayer/profile`.
4.  **Create filing**: The user posts to `/api/v1/filings` attaching their `taxpayer_id`. A new filing generates in the `DRAFT` state.
5.  **Add financial entries**: The user posts individual `INCOME` and `EXPENSE` payloads to `/api/v1/financial-entries`, pointing to the `filing_id`.
6.  **Complete filing lifecycle**: The user hits `PATCH /api/v1/filings/{id}` iteratively to progress the status: `DRAFT` → `READY` → `SUBMITTED` → `VERIFIED`.

---

## 8. STATE MACHINE (FILING)
*   **All states**: `DRAFT`, `READY`, `SUBMITTED`, `VERIFIED`.
*   **Allowed transitions**:
    *   `DRAFT` → `READY`
    *   `READY` → `SUBMITTED`
    *   `SUBMITTED` → `VERIFIED`
*   **Invalid transitions**: Any non-sequential skip (e.g., `DRAFT` → `SUBMITTED`) or backward progression triggers an immediate `400 Bad Request` validation error.

---

## 9. AUTHENTICATION FLOW
*   **Token generation**: Upon `/login`, the service generates a stateless JWT encoded with the `user.id` and a predefined expiration window.
*   **Token usage**: The client injects the token into HTTP headers as `Authorization: Bearer <token>`.
*   **Protected routes**: A global dependency (`get_current_user`) intercepts requests to protected routes. It extracts the JWT, verifies the cryptographic signature, decodes the `user.id`, and automatically rejects invalid/missing tokens with a `401 Unauthorized` exception before business logic executes.

---

## 10. CURRENT LIMITATIONS
*   **No Frontend**: The application currently operates strictly as a headless backend API.
*   **Role-Based Access Control (RBAC)**: Exists in schema (`primary_role`) but complex multi-tier authorization gating (Admin vs User vs CA) is deferred.
*   **Refresh Tokens**: Auth is currently handled via short-lived access tokens; long-lived refresh token rotation is pending implementation.
*   **Missing Integrations**: Third-party compliance hooks (ITR determination logic) are architected but not actively wired.

---

## 11. HOW TO RUN THE SYSTEM
*   **Command to start backend**: Ensure the virtual environment is active, then run: `uvicorn app.main:app --reload`
*   **URL**: The local server deploys to `http://localhost:8000`
*   **How to access Swagger**: The interactive OpenAPI specification is available at `http://localhost:8000/docs`.

---

## 12. SUMMARY
*   **What is complete**: The absolute foundational core of Phase 1 is locked. The backend infrastructure, database configuration, security perimeters, unit testing layers, integration testing suite, and core state machines (Auth, Taxpayer, Filing, Financials) are completely hardened, functioning flawlessly with zero mocked endpoints.
*   **What is pending**: Deep domain engines (ITR Determination, CA Workflow mapping, Evidence Document blob storage hashing), along with final Integration pipelines connecting all services concurrently.
