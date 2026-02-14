# Backend Architecture: Phase-1

## 1. Overview
The MaaV Phase-1 Backend is a high-performance, async-first Python application built on **FastAPI** and **SQLAlchemy (Async)**. It serves as the authoritative source for all business logic and data persistence.

## 2. Directory Structure

### `backend/app/`
- **`main.py`**: The application entry point. Initializes FastAPI, DB connection, and middleware.
- **`api/`**: The Interface Layer. Contains router definitions and depends on Services. **No business logic here.**
- **`core/`**: Infrastructure configuration.
    - `config.py`: Pydantic BaseSettings (Environment variables).
    - `logging.py`: Structured JSON logging setup.
    - `database.py`: SQLAlchemy async engine and session management.
    - `dependencies.py`: Dependency injection providers (e.g., `get_db`).
- **`services/`**: The Business Logic Layer.
    - Implementation of specific use cases (e.g., `CreateTaxpayerService`, `CalculateTaxService`).
    - Orchestrates transactions across multiple Repositories.
- **`repositories/`**: The Persistence Layer.
    - Abstracts database queries using SQLAlchemy.
    - Returns Pydantic models or ORM objects to Services.
- **`engines/`**: The Pure Logic Layer.
    - **Compliance Engine**: Stateless functions that validate data against tax rules.
    - **Calculation Engine**: Stateless functions that compute taxes.
    - These modules **do not** access the database directly.
- **`models/`**: SQLAlchemy ORM definitions (aligned with `db/schema.sql`).
- **`schemas/`**: Pydantic models for data validation (Request/Response DTOs).
- **`middleware/`**: Cross-cutting concerns (Auth, Logging, CORS).
- **`utils/`**: Helper functions (Date formatting, Hashing).

## 3. Dependency Injection
We use FastAPI's built-in DI system for:
- Database Sessions (`get_db`): Ensuring each request gets a fresh, isolated session.
- Current User (`get_current_user`): Extracting user identity from tokens.
- Services: Injecting service instances into API handlers.

## 4. Logging & Monitoring
- **Format**: Structured JSON via `backend/app/core/logging.py`.
- **Level**: Configurable via `LOG_LEVEL` environment variable.
- **Context**: Request ID, User ID, and Endpoint path included in logs.

## 5. Async Database Strategy
- **Driver**: `asyncpg` for high-performance PostgreSQL access.
- **ORM**: SQLAlchemy 2.0+ Async ORM.
- **Migrations**: Alembic for schema evolution.
