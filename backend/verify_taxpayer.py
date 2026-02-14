import sys
import os
import asyncio
import traceback

# Ensure project root is in path
sys.path.append(os.getcwd())

OUTPUT_FILE = "verification_result.txt"

def log(msg):
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)

# Clear previous log
with open(OUTPUT_FILE, "w") as f:
    f.write("Verification Log:\n")

async def verify_model():
    log("Starting verification...")
    try:
        from app.core.database import async_session_factory
        from app.models.taxpayer import TaxpayerProfile
        from sqlalchemy import text, select
        log("Imports successful.")
    except Exception as e:
        log(f"CRITICAL IMPORT ERROR: {e}")
        return

    try:
        async with async_session_factory() as session:
            log("1. Verifying TaxpayerProfile model attributes...")
            try:
                stmt = select(TaxpayerProfile).limit(1)
                await session.execute(stmt)
                log("✅ Select query successful. ORM mapping is valid.")
            except Exception as e:
                log(f"❌ ORM Mapping verification failed: {e}")
                return

            log("\n2. Verifying Schema Alignment (Columns)...")
            # Check specific columns existence via raw SQL
            schema_check = text("""
    SELECT column_name
    FROM information_schema.columns 
    WHERE table_name = 'taxpayer_profiles'
""")
            result = await session.execute(schema_check)
            columns = [row[0] for row in result.fetchall()]
            log(f"DEBUG: Found columns: {columns}")
            
            required_columns = [
                'days_in_india_current_fy', 
                'days_in_india_last_4_years', 
                'has_foreign_income',
                'residential_status',
                'default_tax_regime',
                'aadhaar_link_status',
                'user_id'
            ]
            
            for col in required_columns:
                if col in columns:
                    log(f"✅ Column '{col}' exists.")
                else:
                    log(f"❌ Column '{col}' MISSING in DB!")

            log("\n3. Verifying pan_type removal...")
            if 'pan_type' not in columns:
                 log("✅ Column 'pan_type' correctly removed from DB.")
            else:
                 log(f"❌ Column 'pan_type' still exists in DB!")
    except Exception as e:
        log(f"RUNTIME ERROR: {e}")
        with open(OUTPUT_FILE, "a") as f:
            traceback.print_exc(file=f)

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(verify_model())
    except Exception as e:
        with open("verification_result.txt", "a") as f:
            f.write(f"CRITICAL MAIN ERROR: {e}\n")
            traceback.print_exc(file=f)
