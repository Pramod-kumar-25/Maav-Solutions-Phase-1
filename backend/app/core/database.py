from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from .config import settings

DATABASE_URL = str(settings.SQLALCHEMY_DATABASE_URI)

# When using a transaction pooler (like Supabase's PgBouncer in transaction mode),
# client-side pooling should be disabled to prevent errors with prepared statements 
# and connection state.
# We use NullPool to disable SQLAlchemy's connection pooling.
# For SSL, asyncpg expects strict configuration.

connect_args = {
    "server_settings": {
        "jit": "off",  # Optimization: Disable JIT for simple OLTP queries
        "application_name": "maav-phase1-backend"
    }
}

# Only add SSL if not connecting to localhost
if "localhost" not in DATABASE_URL and "127.0.0.1" not in DATABASE_URL:
    # Supabase uses 'verify-full' or 'require' depending on cert availability.
    # 'require' is safer as it encrypts but doesn't mandate local CA cert unless provided.
    connect_args["ssl"] = "require"

engine = create_async_engine(
    DATABASE_URL,
    poolclass=NullPool,
    echo=False,
    future=True,
    pool_pre_ping=True,  # Re-enabled for resilience
    connect_args=connect_args
)

async_session_factory = async_sessionmaker( # Renaming to match previous usage
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def get_db_session():
    async with async_session_factory() as session:
        yield session
