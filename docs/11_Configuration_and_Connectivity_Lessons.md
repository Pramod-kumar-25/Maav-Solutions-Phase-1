# Configuration and Connectivity Lessons

## 1. Prefer Explicit Configuration Over Silent Correction

### The Decision
In the early stages of Phase-1, we initially implemented logic to automatically rewrite the `DATABASE_URL` (injecting `+asyncpg` or fixing protocols) to make the developer experience "smoother." 

**We have explicitly reversed this decision.**

The configuration logic now **raises an error** if the connection string is not in the exact required format (`postgresql+asyncpg://...`).

### The Rationale
1.  **Deterministic Startup**: A system should either start comfortably with a correct configuration or fail immediately with a clear error. Silent correction masks misconfiguration.
2.  **Production Safety**: "Magic" rewriting logic can behave unpredictably in different environments (e.g., if a new driver is introduced or a proxy changes the URL scheme).
3.  **Debugging Clarity**: If the application cannot connect, the logs should reflect *exactly* what was provided in the environment variables, not a mutated version created at runtime.
4.  **Least Surprise**: An operator providing a `postgresql://` URL expects standard behavior. If the system silently switches drivers behind the scenes, performance characteristics or bug surfaces might change without warning.

### The Standard
The `DATABASE_URL` environment variable must explicitly contain the driver definition:
- ❌ `postgresql://user:pass@host/db` (Ambiguous, implies sync `psycopg2`)
- ✅ `postgresql+asyncpg://user:pass@host/db` (Explicit, Async)

## 2. Supabase Connectivity Strategy

### Session Pooler vs. Direct Connection
We utilize Supabase's **Session Pooler** (via PgBouncer) running on port `5432` (or `6543` depending on network handling) rather than the Direct Connection (`5432`).

- **IPv4 Compatibility**: The Session Pooler provides a stable IPv4 address, which is critical for many deployment environments (including typical Docker containers and some ISPs) that do not support IPv6 natively.
- **Connection Efficiency**: Since we use `SQLAlchemy` with `NullPool` (disabling client-side pooling), we rely on the server-side PgBouncer to manage actual Postgres connections efficiently. This prevents connection exhaustion in serverless or auto-scaling scenarios.

### Logic & SSL Configuration
To ensure secure and reliable connectivity with `asyncpg`:

1.  **Connection String**: Must use the Transaction Pooler port and explicit async driver.
    ```
    DATABASE_URL=postgresql+asyncpg://[user]:[password]@[pooler-host]:[port]/[db-name]
    ```

2.  **SSL Configuration**: 
    - We do **NOT** append `?ssl=true` or `?sslmode=require` to the `DATABASE_URL`. `asyncpg` parsing of these query parameters can be inconsistent or driver-specific.
    - Instead, we pass SSL requirements explicitly via SQLAlchemy's `connect_args`:
      ```python
      # backend/app/core/database.py
      connect_args={
          "server_settings": {"jit": "off"},
          "ssl": "require"  # Only for non-localhost
      }
      ```
    - This separation of concerns (URL for location/auth, Code for transport security policy) ensures robust connections.

3.  **JIT Optimization**: We explicitly disable Postgres JIT (`"jit": "off"`) in `connect_args`. For the typical OLTP workload of Phase-1, JIT compilation adds overhead to initial query planning without benefit.

## 3. Deterministic Infrastructure Principle

### Fail Fast
Configuration errors must stop the application boot process immediately.
- If `DATABASE_URL` is missing: **Crash**.
- If `DATABASE_URL` schema is wrong: **Crash**.
- If `Secret Key` is weak/missing: **Crash**.

### Docs Drive Code
The infrastructure implementations in `core/config.py` and `core/database.py` are not places for improvisation. They must strictly reflect the documented architectural decisions.

### No Hidden Magic
There shall be no "fallback" logic that attempts to guess the user's intent. 
- Example: If a port is missing, do not default to 5432. Force the user to provide it.
- Example: If the driver is missing, do not default to `asyncpg`. force the user to specify it.

This discipline ensures that `env` files are the **single source of truth** for runtime configuration, eliminating "it works on my machine because of a hidden default" scenarios.
