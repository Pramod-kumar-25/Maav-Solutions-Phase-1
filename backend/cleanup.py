import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

async def main():
    engine = create_async_engine('postgresql+asyncpg://postgres.ifrviusnaksvnetjjczj:noshikarinmote2@aws-1-ap-south-1.pooler.supabase.com:5432/postgres')
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check users
        res = await session.execute(text("SELECT id, email, pan FROM users WHERE email='vikram@ca.com' OR pan='ABCDE1234F'"))
        users = res.fetchall()
        print("USERS:", users)
        
        for u in users:
            uid = u[0]
            # Check creds
            cred_res = await session.execute(text(f"SELECT id FROM user_credentials WHERE user_id='{uid}'"))
            creds = cred_res.fetchall()
            print(f"CREDS FOR {uid}:", creds)
            
            if not creds:
                print(f"Orphan user {uid} found! Deleting...")
                await session.execute(text(f"DELETE FROM users WHERE id='{uid}'"))
                await session.commit()
                print("Deleted orphan user.")

asyncio.run(main())
