# Project Philosophy: "Code Law & Engineering Discipline"

## 1. Core Principle
This project embodies **strict engineering discipline**. The architecture is the product, not just the code.

## 2. Documentation-First Engineering Discipline
**CRITICAL MANDATE: DOCUMENTATION IS THE SUPREME AUTHORITY.**

- **Documentation is the source of truth.** If the code does not match the documentation, the code is WRONG.
- **Code must conform to documentation.** Every PR must cite the documentation section it implements.
- **Architecture improvisation is not allowed.** Engineers must not "wing it" or introduce personal architectural preferences.
- **No engineer or tool may invent new layers or abstractions.** The patterns in `docs/` are the ONLY patterns.
- **Any structural change requires updating docs first.** You cannot change the code structure without first updating the HLD/LDM and getting approval.
- **Migration-first, schema-controlled discipline is mandatory.** The database schema is sacred and controlled by `alembic` + `schema.sql`.
- **Supabase UI modifications are prohibited.** Using the GUI to edit schema is a fireable offense in this project context. Code is law.

## 3. Migration-First Strategy
**"Code is Law"**: The database schema is defined in code (`backend/alembic` + `db/schema.sql`).
- **No Manual Changes**: NEVER modify the database schema via GUI tools (Supabase Dashboard, PGAdmin).
- **Auditability**: Every schema change is version-controlled and peer-reviewed.
- **Why?**: To ensure reproducibility across environments (Dev, Test, Prod) and to treat infrastructure as code.

## 4. No Improvisation
- **Follow The Lock**: The `/architecture-lock/` folder contains the "Constitution" of the project.
- **Consult Before Deviating**: If a requirement contradicts the architecture documents, **DO NOT override**. Raise a flag, discuss, update documentation first, THEN code.
- **Mental Model Integrity**: Preserve the "Mental Model" established in documentation. Do not introduce concepts or patterns that contradict it (e.g., adding hidden logic in API handlers).

## 5. Deterministic Systems (Non-AI)
- **Predictability**: The same input MUST always yield the same output.
- **No Hallucinations**: Code logic must be explicit. No "smart guessing" or fuzzy logic.
- **Testing**: Deterministic behavior makes the system highly testable. Unit tests are mandatory for all Engines.

## 6. AI-Ready but Disabled
- **Architecture**: The `backend/app` structure (Engines, Services, API) is designed to be AI-ready.
- **Data Model**: The schema supports vector embeddings (`pgvector` extension installed but unused).
- **Why Disabled?**: To force us to write robust, deterministic foundational code first. AI will be an *enhancement* layer later, not a crutch for bad logic.

## 7. Audit & Human-in-the-Loop
- **Compliance**: Every financial transaction and filing action is treated as a legal record.
- **Traceability**: "Who did what, when, and why?" must be answerable for *every* database write.
- **Confirmation**: The User is the final authority. The system only proposes; the User disposes (confirms).
