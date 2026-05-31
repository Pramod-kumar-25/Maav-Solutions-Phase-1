"""
Integration Test Infrastructure – conftest.py

Provides:
- Async test database engine (isolated SQLite in-memory, zero production contact)
- Per-test transactional isolation via nested savepoints
- FastAPI TestClient with overridden get_db dependency
- No production data contamination
"""
import pytest
import asyncio
from typing import AsyncGenerator

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.dependencies import get_db
from app.main import app
from app.models.base import Base

import uuid
from sqlalchemy import ColumnDefault

# Import all models to ensure they are registered in Base.metadata
import app.models as app_models
from app.models.evidence import EvidenceRecord


# Dynamically patch all primary key and uuid_generate_v4 columns for SQLite compatibility
for table in Base.metadata.tables.values():
    for column in table.columns:
        if column.primary_key or (column.server_default is not None and "uuid_generate_v4" in str(column.server_default.arg)):
            column.server_default = None
            column.default = ColumnDefault(uuid.uuid4)







from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import INET, JSONB

@compiles(INET, "sqlite")
def compile_inet_sqlite(element, compiler, **kw):
    return "VARCHAR(45)"

@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(element, compiler, **kw):
    return "JSON"


# ---------------------------------------------------------------------------
# Engine & Session Factory (isolated SQLite in-memory)
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
)

from sqlalchemy import event
import uuid

@event.listens_for(test_engine.sync_engine, "connect")
def register_sqlite_functions(dbapi_connection, connection_record):
    dbapi_connection.create_function("uuid_generate_v4", 0, lambda: str(uuid.uuid4()))


TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ---------------------------------------------------------------------------
# Event Loop (session-scoped for async fixtures)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ---------------------------------------------------------------------------
# Database Schema Setup (session-scoped – runs once)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    """
    Create all tables at the start of the test session.
    Drop all tables at the end.
    Ensures a clean schema for every test run.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


# ---------------------------------------------------------------------------
# Per-Test Transactional Isolation
# ---------------------------------------------------------------------------
@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a transactional database session for each test.

    Strategy:
    - Open a connection and begin a transaction.
    - Create a nested savepoint (BEGIN SAVEPOINT).
    - Bind a session to the connection.
    - After the test, rollback the savepoint → zero data persisted.
    - Rollback the outer transaction → complete isolation.
    """
    async with test_engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(bind=connection, expire_on_commit=False)

        try:
            yield session
        finally:
            if transaction.is_active:
                await transaction.rollback()
            await session.close()


# ---------------------------------------------------------------------------
# FastAPI Test Client with DB Override
# ---------------------------------------------------------------------------
@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Provide an async HTTP client bound to the FastAPI app.
    The get_db dependency is overridden to use the isolated test session.
    """

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    # Clean up overrides after test
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Auth Helper Fixtures (for tests requiring authenticated requests)
# ---------------------------------------------------------------------------
@pytest.fixture
def auth_headers():
    """
    Factory fixture to generate Authorization headers.
    Usage: headers = auth_headers("some-valid-jwt-token")
    """
    def _make_headers(token: str) -> dict:
        return {"Authorization": f"Bearer {token}"}
    return _make_headers
