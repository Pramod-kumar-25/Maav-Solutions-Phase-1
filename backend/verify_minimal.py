print("Start of script", flush=True)
import sys
import os
print("Imports sys/os done", flush=True)

sys.path.append(os.getcwd())

try:
    print("Importing asyncio...", flush=True)
    import asyncio
    print("Importing sqlalchemy...", flush=True)
    from sqlalchemy import select, text
    print("Importing app.core.database...", flush=True)
    from app.core.database import async_session_maker
    print("Importing app.models.taxpayer...", flush=True)
    from app.models.taxpayer import TaxpayerProfile
    print("✅ All Imports successful", flush=True)
except Exception as e:
    print(f"❌ Import failed: {e}", flush=True)
    sys.exit(1)

async def check():
    print("Inside Async Check...", flush=True)
    try:
        async with async_session_maker() as session:
            print("Session created. Executing query...", flush=True)
            stmt = select(TaxpayerProfile).limit(1)
            await session.execute(stmt)
            print("✅ ORM Model is queryable!", flush=True)
    except Exception as e:
        print(f"❌ Runtime error: {e}", flush=True)

if __name__ == "__main__":
    print("Main block...", flush=True)
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(check())
    except Exception as e:
         print(f"❌ Loop error: {e}", flush=True)
