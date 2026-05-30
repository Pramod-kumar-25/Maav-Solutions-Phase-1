import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

async def get_ca_id():
    engine = create_async_engine('postgresql+asyncpg://postgres.ifrviusnaksvnetjjczj:noshikarinmote2@aws-1-ap-south-1.pooler.supabase.com:5432/postgres')
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        res = await session.execute(text("SELECT id FROM users WHERE email='vikram@ca.com'"))
        print("VIKRAM ID:", res.scalar())

asyncio.run(get_ca_id())
