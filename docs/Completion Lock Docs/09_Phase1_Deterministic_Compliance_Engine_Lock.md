# Completion Lock: Module 5.7 - Deterministic Compliance Engine

> **Status**: LOCKED 🔒
> **Date**: 2026-02-15
> **Scope**: Data Layer, Rule Framework, Repository, Service, API.

## 1. Overview
The Deterministic Compliance Engine provides a framework for evaluating financial data against strict, pre-defined rules. It adheres to the **Agentic Data Layer** philosophy by acting as a pure evaluator with no AI interference in the core logic.

## 2. Key Components

### A. Data Layer (`ComplianceFlag`)
- **Table**: `compliance_flags` (Strict Schema, No Legacy Columns)
- **Key Fields**:
    - `user_id`: Link to User.
    - `financial_year`: Target period (YYYY-YY).
    - `flag_code`: Unique rule identifier (e.g., C001).
    - `severity`: constrained to ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL').
    - `is_resolved`: Boolean status.
- **Migration**: `versions/9dc1fd4443b8_create_compliance_flags_table.py` (Drop & Recreate strategy).

### B. Rule Framework (`BaseComplianceRule`)
- **Interface**: Pure evaluator. Input `List[FinancialEntry]`, Output `Optional[Dict]`.
- **Constraint**: **NO DB ACCESS** inside rules.
- **Implementations**:
    1. `HighTotalExpenseRule`: Checks total expenses > Threshold.
    2. `ExpenseWithoutIncomeRule`: Checks Expense > 0 AND Income == 0.

### C. Service Layer (`ComplianceEngineService`)
- **Orchestration**: Fetches data -> Iterates Rules -> Persists Flags.
- **Idempotency**: Checks for existing **UNRESOLVED** flags before creation.
- **Transaction**: Wraps writes in `async with session.begin():`.
- **Resolution**: Enforces ownership before marking resolved.

### D. API Layer (`api/compliance.py`)
- **Endpoints**:
    - `POST /evaluate`: Trigger checks.
    - `GET /`: List flags.
    - `POST /{id}/resolve`: Resolve flag.
- **Pattern**: Thin Controller. Dependencies injected.

## 3. Boundaries & Constraints (Phase-1)
- **NO AI**: Rules are hardcoded Python classes.
- **NO Tax Computation**: Engine only flags anomalies, does not calculate liability.
- **NO ITR Routing**: No filing logic.
- **NO Automatic Resolution**: Users must explicitly resolve flags.

## 4. Verification
- **Manual Verification**:
    - Migration file reviewed (Dry Run).
    - Service logic verified (Transactions, Idempotency).
    - API wiring verified (Router registration).

## 5. Next Steps
- **Apply Migration**: `alembic upgrade head`.
- **QA Testing**: End-to-End testing with frontend.
