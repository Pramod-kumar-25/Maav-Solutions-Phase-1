# Module 5.8: ITR Determination Engine (Completion Lock)

> **"Code is Law"**: This document certifies the completion of Module 5.8. The logic defined herein is now immutable without a formal change request.

## 1. Objective
Implement a **deterministic, rule-based engine** to select the appropriate Income Tax Return (ITR) form for a user based on their financial data.
**Constraint**: No AI, No Probabilistic Guessing, No Tax Calculation.

## 2. Deliverables

### A. Data Layer (Schema)
-   **Table**: `itr_determinations`
-   **Key Fields**:
    -   `user_id` (UUID, FK to Users)
    -   `financial_year` (String, YYYY-YY)
    -   `itr_type` (String, Enum: ITR-1, ITR-2, ITR-3)
    -   `reason` (Text, Explanatory string)
    -   `is_locked` (Boolean, Default: False)
    -   `determined_at` (Timestamp)
-   **Constraints**:
    -   **Unique**: `(user_id, financial_year)` - One determination per year per user.
    -   **Check**: `itr_type IN ('ITR-1', 'ITR-2', 'ITR-3')`.

### B. Deterministic Rules (The Engine)
The default selection logic is strictly hierarchical:

1.  **ITR-3 (Business)**:
    -   Trigger: Any Income entry with category in `{'BUSINESS', 'PROFESSION', 'FREELANCE'}`.
    -   *Precedence*: Highest.

2.  **ITR-2 (Capital Gains/Foreign/etc - simplified for Phase 1)**:
    -   Trigger: Presence of `SALARY/PENSION` **AND** Other Sources (Non-Business).
    -   *Rationale*: Mixed income (Salary + Other) generally pushes towards ITR-2 in complex scenarios, though simple Interest keeps it ITR-1. For Phase 1 strictness: Mixed = ITR-2.

3.  **ITR-1 (Sahaj)**:
    -   Trigger:
        -   Salary Only.
        -   Other Sources Only.
        -   No Income Found (Default).

### C. Service Layer (`ITRDeterminationService`)
-   **Method**: `determine_itr(session, user_id, financial_year)`
-   **Transactional Safety**:
    -   Entire read-compute-write cycle wrapped in `async with session.begin()`.
-   **Locking Behavior**:
    -   If `is_locked=True` exists -> Raises `ValueError`.
    -   If not locked -> Updates existing record with new determination.
-   **Category Normalization**:
    -   Inputs are normalized via `.strip().upper()` before matching against strict sets.

### D. API Layer
-   **Router**: `backend/app/api/itr.py`
-   **Endpoints**:
    -   `POST /api/v1/itr/determine`: Calculates and persists determination.
    -   `GET /api/v1/itr/?financial_year=...`: Fetches current state.
    -   `POST /api/v1/itr/{financial_year}/lock`: Freezes the determination (User Action).
-   **Validation**:
    -   `financial_year` must match `^\d{4}-\d{2}$`.
    -   Role Access: `INDIVIDUAL` or `BUSINESS` only.

## 3. Scope Boundaries (Phase 1)
-   **NO Filing**: We determine the *form*, we do not generate the XML/JSON for filing.
-   **NO Computation**: We do not calculate tax liability.
-   **NO AI**: Rules are hardcoded.
-   **NO "Real" ITR-4**: Presumptive taxation is out of scope for Phase 1 (treated as ITR-3 or ITR-4 isn't distinguished yet). default Business -> ITR-3.

## 4. Verification
-   **Migration**: `386a56dbabbb_create_itr_determinations_table.py` (Drop & Recreate strategy).
-   **Repo**: `ITRDeterminationRepository` (Pure Persistence).
-   **Service**: `ITRDeterminationService` (Orchestration).

**Status**: 🔒 LOCKED
**Date**: 2026-02-15
