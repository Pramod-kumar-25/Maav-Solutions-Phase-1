import asyncio
import requests
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

async def get_filing_id():
    engine = create_async_engine('postgresql+asyncpg://postgres.ifrviusnaksvnetjjczj:noshikarinmote2@aws-1-ap-south-1.pooler.supabase.com:5432/postgres')
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        res = await session.execute(text("SELECT id FROM users WHERE email='freelance@test.com'"))
        priya_id = res.scalar()
        
        res_filing = await session.execute(text(f"SELECT id FROM filing_cases WHERE user_id='{priya_id}'"))
        return res_filing.scalar()

def assign_ca():
    filing_id = asyncio.run(get_filing_id())
    print("PRIYA FILING ID:", filing_id)
        
    # 1. Login as Priya
    resp = requests.post("http://127.0.0.1:8000/api/v1/auth/login", json={
        "email": "freelance@test.com",
        "password": "My_password@25"
    })
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Grant Consent
    consent_resp = requests.post("http://127.0.0.1:8000/api/v1/consent/", json={
        "purpose": "TAX_FILING_FY_23_24",
        "scope": "FULL_ACCESS",
        "expiry_at": "2026-12-31T23:59:59Z"
    }, headers=headers)
    consent_id = consent_resp.json()["id"]
    print("CONSENT CREATED:", consent_id)
    
    # 3. Assign CA
    assign_resp = requests.post("http://127.0.0.1:8000/api/v1/consent/assignments", json={
        "filing_id": str(filing_id),
        "ca_user_id": "a0f4eb6a-4889-427a-beff-f9544ddd6ad1",
        "consent_id": consent_id
    }, headers=headers)
    
    print("ASSIGNMENT RESULT:", assign_resp.json())

assign_ca()
