# MaaV Solutions: Current State & Future Roadmap

This document serves as the authoritative project status reference for subsequent development phases of the MaaV Solutions platform. It clearly delineates the achievements of Phase-1, the current capabilities of the platform, the final platform vision, and the multi-stage future roadmap.

---

## SECTION 1 – EXECUTIVE SUMMARY

MaaV Solutions Phase-1 is **complete, operational, and verified**.

Parity has been successfully established between the frontend application and the backend service layers. The end-to-end individual taxpayer journey—spanning account registration, secure authentication, multi-step profile setups, real-time ledger records creation, auto-compliance warnings evaluations, locked ITR determinations, and delegated Chartered Accountant (CA) assignments with cryptographic consent receipts—has been fully automated and validated in test and live browser environments.

However, **Phase-1 completion does NOT equal full MaaV vision completion**. Phase-1 establishes the foundation: the compliance database, core state machines, audit trace snapshot engine, and initial taxpayer/CA consent layers. The advanced document extraction features, automated tax health scoring, professional CA workflow tools, and payment gateways are planned for subsequent phases.

---

## SECTION 2 – CURRENT COMPLETED CAPABILITIES

The following operational capabilities are fully implemented in the codebase:

* **Authentication**: Token-based JWT authorization using SHA-256 signatures, user session management, and UI helpers (e.g. show password).
* **User Management**: Unified table models supporting multiple profiles (`INDIVIDUAL` and `CA` roles).
* **Taxpayer Profiles**: Capture of residential parameters (days in India) and active tax regimes (Old vs. New) to feed compliance calculations.
* **Financial Records**: Direct CRUD management of taxable ledger entries (Incomes and Expenses) grouped by category.
* **Compliance Engine**: Dynamic, rules-based engine detecting anomalies, tracking registration limits, and reporting validation warnings.
* **ITR Determination**: Automated engine mapping taxpayer profile configurations to correct ITR forms (ITR-1, ITR-2, ITR-3, ITR-4) and cryptographically locking the determination state.
* **Filing Workflow**: State machine transition tracker driving filings through strict sequential state boundaries (`DRAFT` → `READY_FOR_REVIEW` → `LOCKED` → `SUBMITTED`).
* **Consent Management**: Decentralized consent registry allowing users to grant, review active status of, and revoke access parameters.
* **CA Assignment**: Delegation framework linking taxpayers to active, verified Chartered Accountants under formal consent boundaries.
* **Audit Controls / Evidence Snapshotting**: Automatic evidence capture snapshots generated for crucial actions (granting/revoking consent, changing filing states), storing hashes for immutable verification.
* **Role-Based Access Control (RBAC)**: Active layout filters and frontend route guards blocking unauthorized route and API actions.

---

## SECTION 3 – CURRENT USER JOURNEYS

The current user roles can complete the following distinct workflows:

### 1. Individual Taxpayer
* Register a new account and securely log in.
* Fill in details to calculate residential status and select default Tax Regime (Old/New).
* Initialize a filing case for a specific financial year.
* Input financial transactions (Ledger) to automatically evaluate compliance flags and calculate target ITR type.
* Browse and select from a list of verified CAs, grant active consent for filing access, and assign them to the filing case.
* Submit final filing cases once entries are locked.

### 2. Freelancer / Business User
* Enabled at backend model level (the underlying database schema handles Business tax entities and profile configurations).
* *Note: The frontend UI entry points and onboarding routes for Business users are currently locked/hidden for Phase-1 to ensure a simplified launch for Individuals.*

### 3. Chartered Accountant (CA)
* Register as a verified CA professional.
* Access CA dashboard to monitor assigned client filings.
* View client financial entries, compliance flags, and active consent details.
* Assist in managing filing states based on granted scopes (`READ_ONLY` vs. `FULL_ACCESS`).

---

## SECTION 4 – WHAT WAS DISCOVERED

Reviewing the original, long-term MaaV product requirements against the Phase-1 MVP codebase identifies major features that are **not yet implemented** on the frontend/UI layer:

1. **Document Upload**: Multi-format document ingestion interface (PDF, JPEG, XML).
2. **Document Processing**: Backend OCR/AI extraction pipelines to automatically parse Form 16, AIS/TIS forms, and bank statements.
3. **Tax Health Reports**: Visual graphs, tax savings opportunities, and marginal rate calculations.
4. **Recommendations Engine**: Dynamic prompts suggesting tax-saving investments (Section 80C, 80D, etc.) based on user financial profiles.
5. **Advanced CA Workspace**: Multi-client dashboard with task trackers, file repositories, and collaborative workrooms.
6. **Notification Engine**: Real-time reminders for compliance deadlines, status shifts, and consent expirations (SMS/Email/In-App).
7. **Retention Engine**: Tools designed to re-engage taxpayers and automate recurring yearly filings.
8. **Payments Layer**: Commercial integration supporting filing fees and CA service charges.
9. **Client Communication**: Integrated chat and document feedback loops between taxpayer and CA.
10. **Workflow CRM**: Client management pipelines for CA firms.

---

## SECTION 5 – FINAL MAAV VISION

The intended production end-state of the MaaV Solutions platform will feature:

* **Individual Experience**: Zero-friction tax filing. Taxpayers upload files (Form 16, bank statement), review auto-extracted ledger items, accept an AI-driven tax optimization report, and submit or delegate with one click.
* **CA Experience**: A robust SaaS platform for accounting firms. CAs manage hundreds of clients, communicate via built-in secure channels, request documents, and track compliance metrics through a single dashboard.
* **Document Intelligence**: Deep neural network extraction models parsing any tax document with near-zero error margins.
* **Compliance Intelligence**: Continuous tracking of tax regulations, automatically evaluating filing ledgers against updated tax laws.
* **Tax Health Reports**: Interactive dashboards pointing out financial health scores, deductions optimization, and future net-worth forecasting.
* **Workflow Automation**: AI-triggered transition changes, auto-assigning CAs based on load factors, and automatic e-filing submissions.
* **Payments & Commercials**: Built-in subscription plans for individuals, CAs, and custom business tiers.
* **Retention**: Recurring filing reminders and yearly account migrations.

---

## SECTION 6 – GAP ANALYSIS

Comparison between the current Phase-1 implementation and the final vision:

| Module / System | Phase-1 State | Final Vision Target | Est. Completion |
| :--- | :--- | :--- | :--- |
| **Auth & Security** | JWT Authentication, basic RBAC | MFA, OAuth2, Enterprise SSO | 85% |
| **Filing State Machine** | Complete sequential core transitions | Automated conditional transitions | 90% |
| **Ledger / Financials** | Manual entry creation and tracking | Fully automated bank & statement feed | 40% |
| **Compliance / Rules** | Basic threshold & registration rules | Complete ITR ruleset check & validation | 65% |
| **Document Processing**| Not present on UI | Multi-source OCR & auto-classification | 5% |
| **CA Collaboration** | CA listing, selection, & assignments | Workspace CRM, active chat, team share | 35% |
| **Tax Health & advice** | Not present | Automated advisory reports & planning | 0% |
| **Payments & Billing** | Not present | Multi-tier payment gateway integrations | 0% |
| **Communications** | Backend traces only | In-app, SMS, email notification triggers | 10% |

---

## SECTION 7 – FUTURE DEVELOPMENT ROADMAP

Subsequent development of MaaV Solutions will proceed in the following structured stages:

### Stage A: Document Intelligence Platform
* **Scope**: Build document upload controls. Integrate OCR parsing services to read Form 16 (Part A & B) and bank statement CSVs/PDFs. Map extracted information directly into ledger entries.

### Stage B: Tax Health Report Engine
* **Scope**: Build the visual reporting dashboard. Design engines to analyze ledger patterns and output optimization opportunities, marginal tax graphs, and customized investment advice.

### Stage C: Advanced CA Workspace (CRM)
* **Scope**: Build the workspace for professional CAs. Add client messaging interfaces, multi-CA workspace collaboration logs, shared folders, and progress trackers.

### Stage D: Notification & Retention Engine
* **Scope**: Integrate email/SMS microservices. Build triggers to notify actors of state transitions, impending file deadlocks, and upcoming tax season dates.

### Stage E: Payments & Commercial Layer
* **Scope**: Integrate external payment gateways (e.g. Stripe, Razorpay). Establish paywalls for filings and premium CA consultation models.

### Stage F: Production Hardening
* **Scope**: Implement OAuth2, MFA, and database encryption at rest. Conduct thorough security penetration audits and automated end-to-end pipeline tests.

---

## SECTION 8 – ARCHITECTURAL PRINCIPLES

Future stages must adhere to these architectural foundations:

1. **Automation for Effort, Humans for Accountability**: Technology automates calculations and data entry, but human actors (Taxpayer/CA) must review and authorize each final filing.
2. **Compliance-First**: The rules engine is the ultimate source of truth. Invalid configurations must block filing state transitions.
3. **Consent-First**: Data sharing is strictly opt-in. A CA has zero access without a valid, active consent artifact. The taxpayer retains the right to revoke consent at any moment.
4. **Auditability**: Every key lifecycle change (state change, consent grant/revoke) must write a cryptographic snapshot for compliance logs.

---

## SECTION 9 – NEXT DEVELOPMENT TARGET

The first major post-Phase-1 expansion initiative will be:

**Stage A: Document Intelligence Platform**

Development will focus on building document upload components and integrating the OCR extraction pipeline to automate ledger data entry.
