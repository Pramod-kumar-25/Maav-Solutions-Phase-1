# 🔐 Design Lock: Module 5.13 – CA Workflow & Filing Logic

**Status**: LOCKED 🔒
**Date**: 2026-02-16
**Version**: 2.0 (Strict Zero Migration)

---

## 1. Core Constraints
1.  **Immutable State**: `LOCKED` implies the filing is frozen and approved by the Client. Modification is forbidden.
2.  **Transition Rules (CA Mode)**:
    -   `DRAFT` -> `READY_FOR_REVIEW` (Allowed)
    -   `READY_FOR_REVIEW` -> `LOCKED` (Allowed only via Client Approval)
    -   `LOCKED` -> `SUBMITTED` (Allowed only via CA Submission with Confirmation)
    -   **FORBIDDEN**: `DRAFT` -> `SUBMITTED`, `READY` -> `SUBMITTED`.
3.  **No Schema Changes**: strict adherence to existing `filing_cases` and `user_confirmations` tables.

## 2. Workflow Definition

### Step 1: Preparation (CA)
-   **Action**: `mark_for_approval`
-   **State Transition**: `DRAFT` -> `READY_FOR_REVIEW`
-   **Requirement**: ITR Determination must be valid/locked.

### Step 2: Confirmation (Taxpayer)
-   **Action**: `approve_filing`
-   **State Transition**: `READY_FOR_REVIEW` -> `LOCKED`
-   **Logic**:
    1.  Verify User is the Taxpayer.
    2.  Insert record into `user_confirmations` (IP, Timestamp).
    3.  Update Filing State to `LOCKED`.
    4.  Capture Evidence (Approval Snapshot).

### Step 3: Submission (CA)
-   **Action**: `submit_filing`
-   **State Transition**: `LOCKED` -> `SUBMITTED`
-   **Logic**:
    1.  Verify Filing is `LOCKED`.
    2.  **Enforce**: Fetch latest `user_confirmations` record.
    3.  If missing -> **BLOCK**.
    4.  Update Filing State to `SUBMITTED`.
    5.  Capture Evidence (Submission Snapshot + Confirmation Ref).

## 3. Data Model Strategy
-   **ORM**: Map `UserConfirmation` to existing `user_confirmations` table.
-   **Repo**: New `ConfirmationRepository`.

## 4. Verification Check
-   [x] No Schema Change.
-   [x] No New States.
-   [x] Atomic Evidence Capture.
