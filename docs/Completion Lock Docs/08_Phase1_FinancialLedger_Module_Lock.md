# Infinity Completion Lock: Module 5.6 - Financial Ledger

> **"The Ledger of Truth"**

This document certifies the completion of the **Financial Ledger Module** for MaaV Solutions Phase-1. It locks the architectural decisions, schema, and API contracts for the income and expense intake system.

---

## 1. Architectural Decisions

### A. The Unified Ledger (`financial_entries`)
We rejected the initial design of separate `income_records` and `expense_records` tables in favor of a **Unified Ledger** approach to support future scalability and simpler querying.

- **Table**: `financial_entries`
- **Discriminator**: `entry_type` (Enum: `INCOME` | `EXPENSE`)
- **Philosophy**: Money In vs. Money Out are two sides of the same coin. A single table with an index on `entry_type` allows for faster "Net Cash Flow" calculations and unified reporting.

### B. Persona-Agnostic Design
The Ledger is linked directly to the `User` (Identity), **NOT** to the `TaxpayerProfile` or `BusinessProfile`.
- **Why?**: A User is the legal entity that owns the data. Whether the money comes from Salary (Individual) or Sales (Business) is a property of the *Entry*, not the *Owner*.
- **Constraint**: `user_id` is the Foreign Key.

### C. Source of Truth (Data Sources)
- **`data_sources` Table**: Preserved to track where data came from (AIS, AA, Bank Upload, Manual).
- **Linkage**: While the current `FinancialEntry` table focuses on the *values*, the `description` field currently holds legacy metadata. Future phases will re-establish strict FK links if granular traceback is needed.

---

## 2. Migration & Data Integrity

### A. The Transition
- **Migration ID**: `24bb6ee68183_unify_financial_ledger.py`
- **Strategy**: Manual Safe Transition (No Data Loss).
    1.  Create `financial_entries`.
    2.  **Backfill**:
        -   `income_records` -> `entry_type='INCOME'`
        -   `expense_records` -> `entry_type='EXPENSE'`
    3.  **Drop**: Old `income_records` and `expense_records` tables.
    4.  **Preserve**: `data_sources` table kept for provenance utility.

### B. Safety Mechanisms
- **Constraints**:
    -   `amount >= 0`: Negative values are forbidden (use `entry_type` to denote direction).
    -   `financial_year`: Strict Regex `YYYY-YY`.
    -   `entry_type`: Database-level Check Constraint.

---

## 3. Security Hardening

### A. Role-Based Access Control (RBAC)
- **Rule**: Only `INDIVIDUAL` and `BUSINESS` roles can access the Ledger.
- **Enforcement**: `check_financial_access()` dependency in the Router.
- **Reference**: `UserRole` Enum.

### B. Strict Ownership (The "My Money" Rule)
- **Rule**: A User can **NEVER** delete or view another User's entry.
- **Implementation**:
    -   **Read**: Filtered by `current_user.id` in Service methods (`get_by_user_id`).
    -   **Delete**: Explicit check `if entry.user_id != user_id: raise ValueError` in `delete_entry()`.

---

## 4. Scope & Exclusions (Phase 1)

The following are explicitly **OUT OF SCOPE** for this module and must not be added to this codebase without a new Completion Lock:

1.  **Compliance Logic**: This module accepts data. It does *not* calculate taxes or verify if an expense is deductible.
2.  **ITR Classification**: It does *not* decide which ITR form (1/4) applies.
3.  **AI Classification**: No LLM is used to categorize "Uber Ride" as "Travel Expense". Categories are raw inputs.
4.  **OCR / Parsing**: This module expects structured JSON. File parsing happens elsewhere.

---

## 5. Definition of Done Checklist

- [x] **Schema**: Unified `financial_entries` table created and migrated.
- [x] **Repository**: `FinancialEntryRepository` implemented with async SQLAlchemy.
- [x] **Service**: `FinancialEntryService` with Transactions, Validation, and Ownership logic.
- [x] **API**: REST endpoints (`POST /`, `GET /`, `DELETE /`) with Authorizaton.
- [x] **Security**: RBAC and Row-Level logic verified in code.
- [x] **Documentation**: Mental Model and Implementation Log updated.

---

**Sign-off**:
*   **Module**: 5.6 Financial Ledger
*   **Status**: 🔒 LOCKED
*   **Date**: 2026-02-15
