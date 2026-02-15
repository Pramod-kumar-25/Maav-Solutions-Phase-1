# Module 5.9: Filing Case Engine (Completion Lock)

> **"Code is Law"**: This document certifies the completion of Module 5.9. The logic defined herein is now immutable without a formal change request.

## 1. Objective
Implement a **strict State Machine** to manage the lifecycle of an Income Tax Return (ITR) filing from creation to submission.
**Constraint**: Deterministic transitions only. No backward movement (except explicit rejection loops if added later, but currently linear).

## 2. Deliverables

### A. Data Layer (Schema)
-   **Table**: `filing_cases`
-   **Key Fields**:
    -   `user_id` (UUID, FK Users)
    -   `financial_year` (String, YYYY-YY)
    -   `itr_determination_id` (UUID, FK ITRDeterminations)
    -   `current_state` (String, Enum)
    -   `submitted_at` (Timestamp, Nullable)
-   **Constraints**:
    -   **Unique**: `(user_id, financial_year)` - One active filing per year.
    -   **Unique**: `(itr_determination_id)` - Strict 1:1 with ITR Determination.
    -   **Check**: `current_state IN ('DRAFT', 'READY_FOR_REVIEW', 'LOCKED', 'SUBMITTED')`.

### B. State Machine (The Engine)
The lifecycle is strictly linear in Phase 1:

1.  **DRAFT**: Initial state. Created only after ITR Determination is LOCKED.
2.  **READY_FOR_REVIEW**: User indicates data entry is complete.
3.  **LOCKED**: Final Pre-Submission lock (Digital Signature would happen here).
4.  **SUBMITTED**: Terminal state.

**Validation**:
-   `create_case`: Requires `ITRDetermination.is_locked == True`.
-   `transition_state`: Validates `current -> next` against strict allow-list.

### C. Service Layer (`FilingCaseService`)
-   **Methods**:
    -   `create_case`: transactional creation.
    -   `transition_state`: transactional update with timestamp management.
    -   `get_case`: read access.
-   **Dependencies**: Injects `ITRDeterminationRepository` for cross-module validation.

### D. API Layer
-   **Router**: `backend/app/api/filing.py`
-   **Endpoints**:
    -   `POST /`: Initialize Filing Logic.
    -   `GET /?financial_year=...`: Fetch status.
    -   `POST /{year}/transition`: Execute State Change.
-   **Role Access**: `INDIVIDUAL` or `BUSINESS` only.

## 3. Scope Boundaries (Phase 1)
-   **Internal Workflow Only**: This tracks the *internal* state of the filing.
-   **No External API**: Does NOT connect to the Government Tax Portal yet.
-   **No Json Generation**: The actual ITR JSON generation happens in the next module.

## 4. Verification
-   **Migration**: `bf729ede8c50` (Clean Create Strategy).
-   **Repo**: `FilingCaseRepository` (Pure Persistence).
-   **Service**: `FilingCaseService` (State Machine Logic).

**Status**: 🔒 LOCKED
**Date**: 2026-02-15
