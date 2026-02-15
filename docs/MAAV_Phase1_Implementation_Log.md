# MaaV Solutions Phase-1: Implementation Log

This document tracks the detailed, step-by-step progress of the Phase-1 build, organized by module. It serves as a chronological record of "what was done" to ensure traceability and adherence to the "Code is Law" philosophy.

---

## 📅 SECTION 1 – PROJECT ORIGIN
**Context**: Defining the vision, scope, and engineering philosophy.
**Status**: ✅ COMPLETE

1.  **Requirement Analysis**: Analyzed incomplete client inputs and established a structured framework.
2.  **Documentation Suite**: Created Product Vision, FRS, NFR, Compliance, Data, Security, and Scope documents.
3.  **Strategy Definition**: Explicitly separated AI-native roadmap (Phase 2) from deterministic Non-AI foundation (Phase 1).
4.  **Philosophy Lock**: Enforced "Code is Law" and "Body Before The Brain" principles.

## 📅 SECTION 2 – ARCHITECTURE FOUNDATION
**Context**: Designing the blueprint before writing code.
**Status**: ✅ COMPLETE

1.  **High-Level Design (HLD)**: Created Phase-1 Non-AI HLD.
2.  **Data Modeling**: Developed Logical Data Model (LDM) and Physical Database Schema.
3.  **API Contract**: Defined the API structure and exclusionary boundaries.
4.  **Documentation Discipline**: Locked the "Doc-First" engineering naming conventions.

## 📅 SECTION 3 – INFRASTRUCTURE SETUP
**Context**: Laying the technical rails.
**Status**: ✅ COMPLETE

1.  **Scaffolding**: Established Monorepo structure (`backend/`, `frontend/`, `docs/`).
2.  **Environment**: Configured isolated Python virtual environment.
3.  **Backend Core**: Initialized `FastAPI` (Async) with structured JSON logging (`logging.py`).
4.  **Database Wiring**:
    - Selected **Supabase** (Managed Postgres).
    - Configured **Session Pooler** (Port 6543) for IPv4 compatibility.
    - Enforced **AsyncPG** driver (`postgresql+asyncpg://`).
    - Implemented **SSL** via `connect_args={"ssl": "require"}`.
5.  **Fail-Safe Config**: Implemented strict `pydantic-settings` validation (Refuse to start on invalid config).
6.  **Health Check**: Created `/api/v1/health` endpoint.

## 📅 SECTION 4 – DATABASE OWNERSHIP
**Context**: Establishing "Code is Law" for the Data Layer.
**Status**: ✅ COMPLETE

1.  **Alembic Setup**: Configured Alembic for Async execution.
2.  **Baseline Migration**: Created and applied `initial_schema` (Tables: `audit_logs`, `taxpayer_profiles`, etc.).
3.  **Hardening**: Enforced UUID primary keys, JSONB for flexible storage, and Audit Immutability rules.
4.  **Verification**: Confirmed `alembic_version` table ownership.

---

## 📅 SECTION 5 – APPLICATION LAYER DEVELOPMENT
**Context**: Building the Core Features (Identity, Tax Profile, etc.) using the established foundation.
**Status**: 🚧 IN PROGRESS

### Module 5.1: Identity & Authentication (Completed: 2026-02-14)
**Objective**: Build the secure foundation for user access.

#### Step 1: Infrastructure & Dependencies
1.  **Dependency Installation**: Added `passlib[bcrypt]`, `python-jose[cryptography]`, and `email-validator` to `requirements.txt`.
2.  **Configuration Check**: Verified `SECRET_KEY` and `DATABASE_URL` (AsyncPG) availability in `backend/app/core/config.py`.

#### Step 2: Data Layer (Models)
3.  **Base Model**: Created `backend/app/models/base.py` with SQLAlchemy `declarative_base`.
4.  **User Models**: Created `backend/app/models/user.py` implementing:
    - `User`: Core identity (UUID, Email, Role).
    - `UserCredentials`: Segregated auth secrets.
    - `AuthSession`: Active session tracking.
5.  **Refinement**: Updated `User.account_status` to use correct `server_default=text("'ACTIVE'")`.

#### Step 3: Security Utilities
6.  **Hashing Utils**: Created `backend/app/utils/security.py` using `passlib.context.CryptContext` (bcrypt).

#### Step 4: Repository Layer
7.  **AuthRepository**: Created `backend/app/repositories/auth_repository.py`.
    - Pure CRUD operations for User and Credentials.
    - Added `get_user_by_id` for token resolution.

#### Step 5: Data Transfer Objects (DTOs)
8.  **Pydantic Schemas**: Created `backend/app/schemas/user.py` and `token.py`.

#### Step 6: Service Layer (Business Logic)
9.  **AuthService**: Created `backend/app/services/auth_service.py`.
    - **Transaction Control**: Implemented atomic `async with session.begin()` for Registration.
    - **JWT Generation**: Implemented `python-jose` (HS256) inside Service.

#### Step 7: Interface Layer (API)
10. **Refactored Dependencies**: Updated `deps.py` to use strict Dependency Injection (`get_auth_repository`).
11. **Router**: Created `backend/app/api/auth.py` exposing `/register` and `/login`.
12. **Gatekeeper**: Implemented `get_current_user` in `deps.py` as the **Security Perimeter**.

#### Step 4: Security Hardening
19. **Perimeter Lock**: Confirmed that `deps.py` creates a reusable security boundary.
20. **Documentation**: Created `docs/Completion Lock Docs/02_Phase1_Authentication_Context_Lock.md`.

### Step 5: Authorization Layer (RBAC)
21. **Role Definition**: Defined `UserRole` Enum (INDIVIDUAL, BUSINESS, CA, ADMIN).
22. **Dependency Factory**: Implemented `RoleChecker` class in `deps.py`.
    - **Logic**: Consumes `get_current_user`, verifies `primary_role`.
    - **Enforcement**: Raises HTTP 403 if role mismatch.
    - **Usage**: `Depends(require_role(UserRole.ADMIN))`.

---

### Module 5.2: Taxpayer Profile (Data Layer) (Completed: 2026-02-14)
**Objective**: Establish the persistent storage for user tax profiles and residential classification.

#### Step 1: Database Migration
23. **Schema Evolution**: Created `alembic/versions/d0ae6ede2c2f_update_taxpayer_profile_schema.py`.
    - **Clean Up**: Removed redundant `pan_type` column (derived from User).
    - **Expansion**: Added `days_in_india` and `has_foreign_income` fields.
    - **Safety**: Enforced `NOT NULL` on `has_foreign_income` via backfill strategy (add with default -> drop default).

#### Step 2: ORM Implementation
24. **Model Definition**: Created `backend/app/models/taxpayer.py`.
    - **Strict 1:1**: Enforced unique `user_id`.
    - **Constraints**: Added `CheckConstraint` for `residential_status` (RESIDENT/RNOR/NRI).
    - **Hybrid Property**: Implemented `pan_type` as a read-only derived field.

#### Step 3: Verification
25. **Runtime Validation**: Validated ORM-to-DB alignment using `verify_taxpayer.py` script.
26. **Lock**: Created `docs/Completion Lock Docs/04_Phase1_TaxpayerProfile_DataLayer_Lock.md`.

---

### Module 5.3: Residential Classification Engine (Logic Layer) (Completed: 2026-02-15)
**Objective**: Implement the deterministic logic for Residential Status (Section 6(1)) without external dependencies.

#### Step 1: Engine Implementation
27. **Pure Logic**: Created `backend/app/engines/classification.py`.
    - **No Side Effects**: Function `calculate_residential_status` accepts data, returns Enum.
    - **Logic Limits**: Implemented 182-day and 60+365-day rules (Phase 1).
    - **Forward Compatibility**: Signature accepts citizen/income params for future Phase 2 rules (120-day, Deemed Resident).

#### Step 2: Documentation Lock
28. **Lock**: Created `docs/Completion Lock Docs/05_Phase1_ResidentialClassification_Engine_Lock.md`.

---

### Module 5.4: Taxpayer Profile Integration (Repo/Service/API) (Completed: 2026-02-15)
**Objective**: Connect the data, logic, and interface layers to expose the Taxpayer Profile feature.

#### Step 1: Repository Layer
29. **Persistence**: Created `backend/app/repositories/taxpayer_repository.py`.
    - **Methods**: `get_by_user_id`, `create_profile`.
    - **Isolation**: Pure database interactions, no business logic.

#### Step 2: Service Layer
30. **Orchestration**: Created `backend/app/services/taxpayer_service.py`.
    - **Flow**: 1:1 Check -> Engine Calc -> Business Rule (No NRI) -> Transaction Commit.
    - **Schema**: Created `backend/app/schemas/taxpayer.py`.

#### Step 3: API Layer
31. **Interface**: Created `backend/app/api/taxpayer.py`.
    - **Endpoints**: `POST /profile`, `GET /profile`.
    - **Security**: Enforced `INDIVIDUAL` role via standard RBAC.
    - **Registration**: Mounted in `main.py` at `/api/v1/taxpayer`.

#### Step 4: Final Lock
32. **Module Completion**: Created `docs/Completion Lock Docs/06_Phase1_TaxpayerProfile_Module_Lock.md`.

---

### Module 5.5: Business Profile Module (Repo/Service/API) (Completed: 2026-02-15)
**Objective**: Implement the Business Profile system for Non-Individual entities.

#### Step 1: Data Layer
33. **Schema**: Created `business_profiles` table via Alembic (`9a54bfb1c477`).
    - **Model**: `backend/app/models/business.py`.
    - **Constraint**: Strict 1:1 with User.

#### Step 2: Repository Layer
34. **Persistence**: Created `backend/app/repositories/business_repository.py`.
    - **Methods**: `get_by_user_id`, `create_profile`.

#### Step 3: Service Layer
35. **Orchestration**: Created `backend/app/services/business_service.py`.
    - **Validation**:
        - **Block 'P'**: Individuals cannot create Business Profiles (Phase 1).
        - **Match Char**: Constitution must match PAN 4th character.

#### Step 4: API Layer
36. **Interface**: Created `backend/app/api/business.py`.
    - **Endpoints**: `POST /profile`, `GET /profile`.
    - **Role**: Restricted to `BUSINESS` role.
    - **Router**: Registered at `/api/v1/business`.

#### Step 5: Final Lock
37. **Module Completion**: Created `docs/Completion Lock Docs/07_Phase1_BusinessProfile_Module_Lock.md`.

---

## 📅 SECTION 5.6: Income & Expense Intake Module (Data/Repo/Service/API)
**Context**: Implementing the unified system for Income and Expense intake.
**Status**: ✅ COMPLETE

### Module 5.6: Income & Expense Intake Module (Completed: 2026-02-15)
**Objective**: Create a robust, persona-agnostic ledger for financial tracking.

#### Step 1: Architectural Pivot
38. **Unified Design**: Replaced separate `income_records` and `expense_records` with a single `financial_entries` table.
    - **Why**: Simplified querying and clearer "Net Cash Flow" logic.
    - **Models**: `backend/app/models/financials.py`.

#### Step 2: Safe Migration
39. **Manual Transition**: Created `alembic/versions/24bb6ee68183_unify_financial_ledger.py`.
    - **Backfill Strategy**: Migrated existing data to new structure before dropping old tables.
    - **Data Integrity**: Preserved `data_sources`.

#### Step 3: Stack Implementation
40. **Repository**: `FinancialEntryRepository` (Async/SQLAlchemy).
41. **Service**: `FinancialEntryService` (Transactions, Validation, Ownership Checks).
42. **API**: `backend/app/api/financials.py` (RBAC: Individual/Business).

#### Step 4: Final Lock
43. **Module Completion**: Created `docs/Completion Lock Docs/08_Phase1_Income_Expense_Intake_Module_Lock.md`.

---

### Module 5.7: Deterministic Compliance Engine (Data/Repo/Service/API) (Completed: 2026-02-15)
**Objective**: Implement a strict, non-AI rule engine to flag financial anomalies.

#### Step 1: Data Layer
44. **Schema**: Created `compliance_flags` table (Strict Schema, Drop/Recreate Strategy).
    - **Model**: `backend/app/models/compliance.py`.
    - **Migration**: `versions/9dc1fd4443b8_create_compliance_flags_table.py`.

#### Step 2: Rule Framework
45. **Pure Logic**: Implemented `BaseComplianceRule` interface (No DB Access).
    - **Rules**: `HighTotalExpenseRule`, `ExpenseWithoutIncomeRule`.

#### Step 3: Service Layer
46. **Orchestration**: `ComplianceEngineService`.
    - **Idempotency**: Prevents duplicate flags (Unresolved only).
    - **Transaction**: Explicit `async with session.begin()` for all writes.

#### Step 4: API Layer
47. **Interface**: `backend/app/api/compliance.py`.
    - **Endpoints**: `/evaluate`, `/`, `/{id}/resolve`.
    - **Strict Layering**: Router depends ONLY on Service.

#### Step 5: Final Lock
48. **Module Completion**: Created `docs/Completion Lock Docs/09_Phase1_Deterministic_Compliance_Engine_Lock.md`.

---

### Module 5.8: ITR Determination Engine (Data/Repo/Service/API) (Completed: 2026-02-15)
**Objective**: Deterministically select ITR Form (ITR-1/2/3) based on financial ledger.

#### Step 1: Data Layer
49. **Schema**: Created `itr_determinations` table.
    - **Model**: `backend/app/models/itr.py`.
    - **Migration**: `versions/386a56dbabbb_create_itr_determinations_table.py` (Safe Reset Strategy).

#### Step 2: Service Layer (The Engine)
50. **Logic**: `ITRDeterminationService`.
    - **Rules**: Business -> ITR-3, Mixed -> ITR-2, Salary/Other -> ITR-1.
    - **Locking**: Implemented `lock_determination` workflow.
    - **Transaction**: Atomic read-compute-write cycle.

#### Step 3: API Layer
51. **Interface**: `backend/app/api/itr.py`.
    - **Endpoints**: `/determine`, `/`, `/{year}/lock`.
    - **Validation**: Strict YYYY-YY regex and Role checks.

#### Step 4: Final Lock
52. **Module Completion**: Created `docs/Completion Lock Docs/10_Phase1_ITR_Determination_Engine_Lock.md`.

---

### Module 5.9: Filing Case Engine (Data/Repo/Service/API) (Completed: 2026-02-15)
**Objective**: strict State Machine to manage the lifecycle of an Income Tax Return (ITR) filing.

#### Step 1: Data Layer
53. **Schema**: Created `filing_cases` table.
    - **Constraints**: Enforced 1:1 with `itr_determinations` and unique `(user_id, financial_year)`.
    - **Migration**: `bf729ede8c50` (Manual cleanup of pre-existing conflict, then clean create).

#### Step 2: Repository Layer
54. **Persistence**: `FilingCaseRepository`.
    - **Methods**: Pure CRUD for filing definitions.

#### Step 3: Service Layer (State Machine)
55. **Logic**: `FilingCaseService`.
    - **Transitions**: DRAFT -> REVIEW -> LOCKED -> SUBMITTED.
    - **Validation**: Enforced `ITRDetermination.is_locked` checks.
    - **Dependencies**: Cross-module validation using `ITRDeterminationRepository`.

#### Step 4: API Layer
56. **Interface**: `backend/app/api/filing.py`.
    - **Endpoints**: `/`, `/transition`.
    - **Security**: RBAC (Individual/Business).

#### Step 5: Final Lock
57. **Module Completion**: Created `docs/Completion Lock Docs/11_Phase1_Filing_Case_Engine_Lock.md`.

---

