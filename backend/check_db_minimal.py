import sys
import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Hardcoded for test - reading from .env manually would be better but keeping it simple for isolation
DB_URL = "postgresql+asyncpg://postgres:1999999999@localhost:6543/postgres"

async def check_db():
    print(f"Connecting to {DB_URL}...", flush=True)
    try:
        engine = create_async_engine(DB_URL)
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print(f"✅ DB Connection Successful: {result.scalar()}", flush=True)
    except Exception as e:
        print(f"❌ DB Connection Failed: {e}", flush=True)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(check_db())
