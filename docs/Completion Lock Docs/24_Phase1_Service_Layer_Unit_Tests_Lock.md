# Section 7: Unit Tests for Service Layer – Complete Lock

## 1. Architectural Mandate
Establish a deterministic, fully isolated testing harness for the Phase-1 service layer. Every service orchestration path—success and failure—must be validated without database connectivity, using mocked repositories and explicit domain exceptions exclusively.

## 2. Implementation Boundaries
- **Target Components**: `tests/unit/services/test_create_taxpayer_service.py`, `tests/unit/services/test_filing_service.py`, `tests/unit/services/test_financial_entry_service.py`
- **Excluded**: API route testing, integration testing, real database connections, dependency injection wiring

## 3. Verified Coverage

### 3.1 TaxpayerProfileService (`test_create_taxpayer_service.py` — 5 tests)
| Test Case | Behavior | Exception | Write Guard |
|---|---|---|---|
| `test_create_taxpayer_success` | Valid creation, `result.id is not None` | — | `create` called once |
| `test_create_taxpayer_duplicate` | Existing profile blocks creation | `DuplicateResourceError` | `call_count == 0` |
| `test_create_taxpayer_invalid_pan_type` | Non-individual PAN rejected | `ValidationError` | `call_count == 0` |
| `test_create_taxpayer_user_not_found` | Missing user halts flow | `NotFoundError` | `call_count == 0` |
| `test_create_taxpayer_sets_default_values` | Schema defaults populated | — | `create` called once |

### 3.2 FilingService – State Machine (`test_filing_service.py` — 8 tests)
| Test Case | Behavior | Exception | Write Guard |
|---|---|---|---|
| `test_create_filing_success` | Filing starts in DRAFT, `result.id is not None` | — | `create` called once |
| `test_valid_state_transition_draft_to_ready` | DRAFT → READY | — | `update` called once |
| `test_invalid_state_transition` | DRAFT → VERIFIED blocked | `ValidationError` | `call_count == 0` |
| `test_submit_without_ready_state` | DRAFT → SUBMITTED blocked | `ValidationError` | `call_count == 0` |
| `test_verify_without_submission` | READY → VERIFIED blocked | `ValidationError` | `call_count == 0` |
| `test_duplicate_submission` | SUBMITTED → SUBMITTED blocked | `DuplicateResourceError` / `ValidationError` | `call_count == 0` |
| `test_transition_filing_not_found` | Missing filing halts flow | `NotFoundError` | `call_count == 0` |
| `test_successful_full_flow` | DRAFT → READY → SUBMITTED → VERIFIED | — | `update` called once per step |

### 3.3 FinancialEntryService (`test_financial_entry_service.py` — 11 tests)
| Test Case | Behavior | Exception | Write Guard |
|---|---|---|---|
| `test_create_entry_success` | Valid INCOME entry created | — | `create_entry` called once |
| `test_create_expense_entry_success` | Valid EXPENSE entry created | — | `create_entry` called once |
| `test_negative_amount_rejected` | Negative INCOME amount blocked | `ValidationError` | `call_count == 0` |
| `test_invalid_type_rejected` | Type "REFUND" blocked | `ValidationError` | `call_count == 0` |
| `test_fetch_entries_by_user` | Retrieves mixed entry list | — | — |
| `test_get_entry_not_found` | Missing entry raises error | `NotFoundError` | — |
| `test_zero_amount_accepted` | Boundary: `0.00` passes `>= 0` | — | `create_entry` called once |
| `test_create_expense_success` | EXPENSE-specific creation | — | `create_entry` called once |
| `test_expense_negative_amount` | Negative EXPENSE amount blocked | `ValidationError` | `call_count == 0` |
| `test_expense_invalid_type` | Type "DEDUCTION" blocked | `ValidationError` | `call_count == 0` |
| `test_fetch_expense_entries` | Filtered EXPENSE retrieval | — | — |

## 4. Architectural Guarantees
- [x] All core services covered: Taxpayer, Filing, Financial Entry
- [x] All repository dependencies mocked using `AsyncMock` — zero database interaction
- [x] No string-based assertions on exception messages — exception type validation only
- [x] Only domain exceptions used: `ValidationError`, `NotFoundError`, `DuplicateResourceError`
- [x] All failure paths enforce `repo.write_method.call_count == 0`
- [x] State machine transitions strictly enforced (DRAFT → READY → SUBMITTED → VERIFIED)
- [x] Invalid transitions blocked with zero state mutation
- [x] Boundary conditions validated (zero amount, missing entities, duplicate resources)
- [x] Arrange–Act–Assert pattern consistently followed across all 24 test cases

## 5. Artifacts Locked
- `backend/tests/unit/services/test_create_taxpayer_service.py` (5 tests)
- `backend/tests/unit/services/test_filing_service.py` (8 tests)
- `backend/tests/unit/services/test_financial_entry_service.py` (11 tests)

## 6. Total Test Count: 24
