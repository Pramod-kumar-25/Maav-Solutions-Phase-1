import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
import uuid
from datetime import datetime, timezone

async def fix_assignment():
    engine = create_async_engine('postgresql+asyncpg://postgres.ifrviusnaksvnetjjczj:noshikarinmote2@aws-1-ap-south-1.pooler.supabase.com:5432/postgres')
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        res = await session.execute(text("SELECT id FROM users WHERE email='freelance@test.com'"))
        priya_id = res.scalar()
        
        res_filing = await session.execute(text(f"SELECT id FROM filing_cases WHERE user_id='{priya_id}'"))
        filing_id = res_filing.scalar()
        
        # Get consent ID if exists
        res_consent = await session.execute(text(f"SELECT id FROM consent_artifacts WHERE user_id='{priya_id}' LIMIT 1"))
        consent_id = res_consent.scalar()
        if not consent_id:
            consent_id = uuid.uuid4()
            await session.execute(text(f"INSERT INTO consent_artifacts (id, user_id, purpose, scope, expiry_at, status, granted_at) VALUES ('{consent_id}', '{priya_id}', 'TAX', 'FULL', '2026-12-31', 'ACTIVE', now())"))
            
        ca_user_id = 'a0f4eb6a-4889-427a-beff-f9544ddd6ad1'
        
        # Check assignment
        res_assign = await session.execute(text(f"SELECT id FROM ca_assignments WHERE filing_id='{filing_id}' AND ca_user_id='{ca_user_id}'"))
        assign_id = res_assign.scalar()
        if not assign_id:
            assign_id = uuid.uuid4()
            await session.execute(text(f"INSERT INTO ca_assignments (id, filing_id, ca_user_id, consent_id, status, assigned_at) VALUES ('{assign_id}', '{filing_id}', '{ca_user_id}', '{consent_id}', 'ACTIVE', now())"))
        
        await session.commit()
        print("ASSIGNMENT FORCED IN DB. CA ID:", ca_user_id, "FILING:", filing_id)

asyncio.run(fix_assignment())
