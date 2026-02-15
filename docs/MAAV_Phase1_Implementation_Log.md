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

## 📅 SECTION 5.4: [Next Module Name]
**Context**: [TBD]
**Status**: 🕒 PENDING
- [ ] **Taxpayer Profile Service & API**
- [ ] **Business Entity Module**
- [ ] **Income & Expense Intake Module**
- [ ] **Deterministic Compliance Engine**
- [ ] **ITR Determination Logic**
- [ ] **Filing Lifecycle Management**
- [ ] **CA Assignment & Consent Workflow**
