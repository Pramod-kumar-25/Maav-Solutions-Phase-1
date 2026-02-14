# Database Strategy: Phase-1

## 1. Overview
The database for MaaV Phase-1 is **Supabase (Managed PostgreSQL)**. However, we treat it strictly as a **Managed Postgres Service**, relying on our own migration scripts and application logic rather than Supabase's UI features.

## 2. Infrastructure
- **Provider**: Supabase.
- **Engine**: PostgreSQL 15+.
- **Extensions**:
    - `uuid-ossp`: Enabled for UUID primary keys.
    - `pgcrypto`: For hashing/encryption if needed.
    - `pgvector`: Not used in Phase-1 (Non-AI), but kept for future.

## 3. Migration First Philosophy
**"Code is Law"**: Database changes are strictly code-driven.
- **Development**: New migrations are created via `alembic revision --autogenerate`.
- **Review**: Migration scripts (`.py` files in `backend/alembic/versions`) are reviewed for correctness.
- **Application**: `alembic upgrade head` applies changes in order.
- **NO UI Edits**: Using the Supabase Table Editor to change schema is strictly forbidden. It creates drift and breaks reproducibility.

## 4. The Authoritative Schema
The file `db/schema.sql` serves as the **Authoritative Physical Schema** reference documentation.
- It MUST be kept in sync with the actual database state reflected by Alembic migrations.
- It is the source of truth for understanding the entire data model at a glance.

## 5. Constraint Enforcement
We leverage PostgreSQL's robust constraint engine:
- **Foreign Keys**: Enforced everywhere. `ON DELETE CASCADE` for child records (e.g., Income for a User), `ON DELETE SET NULL` for audit trails.
- **Check Constraints**: Used for data validity (e.g., `amount >= 0`, `status IN (...)`).
- **Unique Constraints**: Used for business rules (e.g., One User -> One Taxpayer Profile, Unique GSTIN).

## 6. Connection Management
- **Pooler**: PgBouncer (Transaction mode) provided by Supabase.
- **Driver**: `asyncpg` for high-concurrency async support in FastAPI.
- **Settings**: Defined in `backend/app/core/database.py` with `pool_size`, `max_overflow`.
