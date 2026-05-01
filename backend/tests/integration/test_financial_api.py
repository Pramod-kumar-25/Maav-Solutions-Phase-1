import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def _setup_env(client: AsyncClient, email: str):
    """Helper to register user, login, create taxpayer, and create a filing."""
    password = "StrongPassword123!"
    
    # 1. Register
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Financial User", "primary_role": "INDIVIDUAL"}
    )
    
    # 2. Login
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password}
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Create Taxpayer Profile
    prof_resp = await client.post(
        "/api/v1/taxpayer/profile",
        json={
            "days_in_india_current_fy": 182,
            "days_in_india_last_4_years": 400,
            "has_foreign_income": False,
            "default_tax_regime": "NEW",
            "aadhaar_link_status": True
        },
        headers=headers
    )
    taxpayer_id = prof_resp.json()["id"]
    
    # 4. Create Filing
    filing_resp = await client.post(
        "/api/v1/filings",
        json={"taxpayer_id": taxpayer_id, "financial_year": "2023-24"},
        headers=headers
    )
    filing_id = filing_resp.json()["id"]
    
    return token, headers, filing_id


async def test_create_income_success(client: AsyncClient):
    """
    Test Case: test_create_income_success
    - Create INCOME entry
    - Validate response structure
    """
    _, headers, filing_id = await _setup_env(client, "income@example.com")
    
    payload = {
        "filing_id": filing_id,
        "type": "INCOME",
        "amount": 50000.0,
        "description": "Salary"
    }
    
    response = await client.post("/api/v1/financial-entries", json=payload, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["type"] == "INCOME"
    assert data["amount"] == 50000.0


async def test_create_expense_success(client: AsyncClient):
    """
    Test Case: test_create_expense_success
    - Create EXPENSE entry
    - Validate response
    """
    _, headers, filing_id = await _setup_env(client, "expense@example.com")
    
    payload = {
        "filing_id": filing_id,
        "type": "EXPENSE",
        "amount": 10000.0,
        "description": "Office Supplies"
    }
    
    response = await client.post("/api/v1/financial-entries", json=payload, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["type"] == "EXPENSE"
    assert data["amount"] == 10000.0


async def test_negative_amount_rejected(client: AsyncClient):
    """
    Test Case: test_negative_amount_rejected
    - Provide negative amount
    - Expect 400
    """
    _, headers, filing_id = await _setup_env(client, "negative@example.com")
    
    payload = {
        "filing_id": filing_id,
        "type": "INCOME",
        "amount": -500.0,
        "description": "Negative value"
    }
    
    response = await client.post("/api/v1/financial-entries", json=payload, headers=headers)
    
    assert response.status_code == 400
    assert "detail" in response.json()


async def test_invalid_type_rejected(client: AsyncClient):
    """
    Test Case: test_invalid_type_rejected
    - Invalid type
    - Expect 400
    """
    _, headers, filing_id = await _setup_env(client, "invalid_type@example.com")
    
    payload = {
        "filing_id": filing_id,
        "type": "INVALID_TYPE",
        "amount": 1000.0,
        "description": "Wrong type"
    }
    
    response = await client.post("/api/v1/financial-entries", json=payload, headers=headers)
    
    assert response.status_code == 400
    assert "detail" in response.json()


async def test_get_financial_entries(client: AsyncClient):
    """
    Test Case: test_get_financial_entries
    - Fetch entries for user
    - Validate list response
    """
    _, headers, filing_id = await _setup_env(client, "get_entries@example.com")
    
    # Create an entry first
    await client.post(
        "/api/v1/financial-entries", 
        json={"filing_id": filing_id, "type": "INCOME", "amount": 2000.0, "description": "Bonus"}, 
        headers=headers
    )
    
    response = await client.get(f"/api/v1/financial-entries?filing_id={filing_id}", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(entry["amount"] == 2000.0 for entry in data)


async def test_financial_entry_not_found(client: AsyncClient):
    """
    Test Case: test_financial_entry_not_found
    - Fetch non-existing entry
    - Expect 404
    """
    _, headers, _ = await _setup_env(client, "not_found@example.com")
    
    response = await client.get("/api/v1/financial-entries/00000000-0000-0000-0000-000000000000", headers=headers)
    
    assert response.status_code == 404
    assert "detail" in response.json()


async def test_financial_unauthorized_access(client: AsyncClient):
    """
    Test Case: test_financial_unauthorized_access
    - Call without token
    - Expect 401
    """
    payload = {
        "filing_id": "00000000-0000-0000-0000-000000000000",
        "type": "INCOME",
        "amount": 5000.0,
        "description": "Missing auth"
    }
    
    response = await client.post("/api/v1/financial-entries", json=payload)
    
    assert response.status_code == 401
    assert "detail" in response.json()


async def test_get_financial_entries_unauthorized(client: AsyncClient):
    """
    Test Case: test_get_financial_entries_unauthorized
    - Call GET without token
    - Expect 401
    """
    response = await client.get("/api/v1/financial-entries?filing_id=00000000-0000-0000-0000-000000000000")
    
    assert response.status_code == 401
    assert "detail" in response.json()
