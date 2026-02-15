import asyncio
import sys
from sqlalchemy import text
from app.core.database import async_session_factory

async def main():
    async with async_session_factory() as session:
        print("Checking filing_cases table...")
        try:
            result = await session.execute(text("SELECT count(*) FROM filing_cases"))
            count = result.scalar()
            print(f"Table 'filing_cases' exists with {count} rows.")
            
            if count == 0:
                print("Table is empty. Dropping it to allow clean migration...")
                await session.execute(text("DROP TABLE filing_cases CASCADE"))
                await session.commit()
                print("Table 'filing_cases' dropped successfully.")
            else:
                print("WARNING: Table is NOT empty. Aborting drop.")
                sys.exit(1)
        except Exception as e:
            if "undefined table" in str(e) or "does not exist" in str(e):
                print("Table 'filing_cases' does not exist.")
            else:
                print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
