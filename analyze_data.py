import asyncio
import sys
import os

# Add backend to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from sqlalchemy import text, inspect
from app.core.database import engine

async def analyze_financial_tables():
    async with engine.connect() as conn:
        print("--- Analysis Report ---")
        
        # 1. Row Counts
        for table in ['income_records', 'expense_records']:
            result = await conn.execute(text(f"SELECT count(*) FROM {table}"))
            count = result.scalar()
            print(f"Table '{table}': {count} rows")

        # 2. Schema Inspection (NOT NULL constraints)
        print("\n--- Column Constraints ---")
        # querying information_schema because inspect calls might be synchronous or complex in async context without run_sync
        query = text("""
            SELECT table_name, column_name, is_nullable 
            FROM information_schema.columns 
            WHERE table_name IN ('income_records', 'expense_records') 
            AND column_name IN ('taxpayer_id', 'business_id')
        """)
        result = await conn.execute(query)
        rows = result.fetchall()
        for row in rows:
            print(f"Table: {row.table_name}, Column: {row.column_name}, Nullable: {row.is_nullable}")

if __name__ == "__main__":
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(analyze_financial_tables())
    except Exception as e:
        import traceback
        traceback.print_exc()
