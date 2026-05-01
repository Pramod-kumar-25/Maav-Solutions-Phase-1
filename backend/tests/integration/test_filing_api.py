import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def _setup_user_and_taxpayer(client: AsyncClient, email: str):
    """Helper to register user, login, and create taxpayer profile."""
    password = "StrongPassword123!"
    
    # Register
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Filing User", "primary_role": "INDIVIDUAL"}
    )
    
    # Login
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password}
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create Taxpayer Profile
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
    # Extract the taxpayer_id for filing association
    taxpayer_id = prof_resp.json()["id"]
    return token, headers, taxpayer_id


async def test_create_filing_success(client: AsyncClient):
    """
    Test Case: test_create_filing_success
    - Create filing
    - Expect initial state = DRAFT
    """
    _, headers, taxpayer_id = await _setup_user_and_taxpayer(client, "filing_create@example.com")
    
    payload = {
        "taxpayer_id": taxpayer_id,
        "financial_year": "2023-24"
    }
    
    response = await client.post("/api/v1/filings", json=payload, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["status"] == "DRAFT"
    assert data["financial_year"] == "2023-24"


async def test_valid_state_transition(client: AsyncClient):
    """
    Test Case: test_valid_state_transition
    - DRAFT → READY
    - Ensure state updates correctly
    """
    _, headers, taxpayer_id = await _setup_user_and_taxpayer(client, "filing_transition@example.com")
    
    # 1. Create filing (DRAFT)
    create_resp = await client.post(
        "/api/v1/filings", 
        json={"taxpayer_id": taxpayer_id, "financial_year": "2023-24"}, 
        headers=headers
    )
    filing_id = create_resp.json()["id"]
    
    # 2. Transition to READY
    trans_resp = await client.patch(
        f"/api/v1/filings/{filing_id}",
        json={"status": "READY"},
        headers=headers
    )
    
    assert trans_resp.status_code == 200
    data = trans_resp.json()
    assert "id" in data
    assert data["status"] == "READY"


async def test_invalid_state_transition(client: AsyncClient):
    """
    Test Case: test_invalid_state_transition
    - Attempt DRAFT → VERIFIED
    - Expect error
    """
    _, headers, taxpayer_id = await _setup_user_and_taxpayer(client, "filing_invalid_skip@example.com")
    
    # 1. Create filing (DRAFT)
    create_resp = await client.post(
        "/api/v1/filings", 
        json={"taxpayer_id": taxpayer_id, "financial_year": "2023-24"}, 
        headers=headers
    )
    filing_id = create_resp.json()["id"]
    
    # 2. Attempt invalid transition (DRAFT -> VERIFIED directly)
    trans_resp = await client.patch(
        f"/api/v1/filings/{filing_id}",
        json={"status": "VERIFIED"},
        headers=headers
    )
    
    assert trans_resp.status_code == 400
    assert "detail" in trans_resp.json()


async def test_submit_without_ready(client: AsyncClient):
    """
    Test Case: test_submit_without_ready
    - Attempt submission without READY state
    - Expect failure
    """
    _, headers, taxpayer_id = await _setup_user_and_taxpayer(client, "filing_skip_ready@example.com")
    
    # 1. Create filing (DRAFT)
    create_resp = await client.post(
        "/api/v1/filings", 
        json={"taxpayer_id": taxpayer_id, "financial_year": "2023-24"}, 
        headers=headers
    )
    filing_id = create_resp.json()["id"]
    
    # 2. Attempt DRAFT -> SUBMITTED directly
    trans_resp = await client.patch(
        f"/api/v1/filings/{filing_id}",
        json={"status": "SUBMITTED"},
        headers=headers
    )
    
    assert trans_resp.status_code == 400
    assert "detail" in trans_resp.json()


async def test_verify_without_submission(client: AsyncClient):
    """
    Test Case: test_verify_without_submission
    - Attempt verify before submission
    - Expect failure
    """
    _, headers, taxpayer_id = await _setup_user_and_taxpayer(client, "filing_skip_submit@example.com")
    
    # 1. Create filing (DRAFT)
    create_resp = await client.post(
        "/api/v1/filings", 
        json={"taxpayer_id": taxpayer_id, "financial_year": "2023-24"}, 
        headers=headers
    )
    filing_id = create_resp.json()["id"]
    
    # 2. Transition to READY
    await client.patch(f"/api/v1/filings/{filing_id}", json={"status": "READY"}, headers=headers)
    
    # 3. Attempt READY -> VERIFIED directly (skipping SUBMITTED)
    trans_resp = await client.patch(
        f"/api/v1/filings/{filing_id}",
        json={"status": "VERIFIED"},
        headers=headers
    )
    
    assert trans_resp.status_code == 400
    assert "detail" in trans_resp.json()


async def test_duplicate_submission(client: AsyncClient):
    """
    Test Case: test_duplicate_submission
    - Attempt multiple submissions
    - Expect error
    """
    _, headers, taxpayer_id = await _setup_user_and_taxpayer(client, "filing_duplicate@example.com")
    
    # 1. Create filing (DRAFT)
    create_resp = await client.post(
        "/api/v1/filings", 
        json={"taxpayer_id": taxpayer_id, "financial_year": "2023-24"}, 
        headers=headers
    )
    filing_id = create_resp.json()["id"]
    
    # 2. Progress to READY
    await client.patch(f"/api/v1/filings/{filing_id}", json={"status": "READY"}, headers=headers)
    
    # 3. Progress to SUBMITTED
    first_submit = await client.patch(f"/api/v1/filings/{filing_id}", json={"status": "SUBMITTED"}, headers=headers)
    assert first_submit.status_code == 200
    data = first_submit.json()
    assert "id" in data
    assert data["status"] == "SUBMITTED"
    
    # 4. Attempt to SUBMIT again
    second_submit = await client.patch(f"/api/v1/filings/{filing_id}", json={"status": "SUBMITTED"}, headers=headers)
    
    assert second_submit.status_code == 400
    assert "detail" in second_submit.json()


async def test_full_filing_lifecycle(client: AsyncClient):
    """
    Test Case: test_full_filing_lifecycle
    - Create filing (DRAFT)
    - Transition to READY
    - Transition to SUBMITTED
    - Transition to VERIFIED
    - Assert final state = VERIFIED
    """
    _, headers, taxpayer_id = await _setup_user_and_taxpayer(client, "filing_full_lifecycle@example.com")
    
    # 1. Create (DRAFT)
    create_resp = await client.post(
        "/api/v1/filings", 
        json={"taxpayer_id": taxpayer_id, "financial_year": "2023-24"}, 
        headers=headers
    )
    filing_id = create_resp.json()["id"]
    
    # 2. Transition -> READY
    ready_resp = await client.patch(f"/api/v1/filings/{filing_id}", json={"status": "READY"}, headers=headers)
    assert ready_resp.status_code == 200
    assert ready_resp.json()["status"] == "READY"
    
    # 3. Transition -> SUBMITTED
    sub_resp = await client.patch(f"/api/v1/filings/{filing_id}", json={"status": "SUBMITTED"}, headers=headers)
    assert sub_resp.status_code == 200
    assert sub_resp.json()["status"] == "SUBMITTED"
    
    # 4. Transition -> VERIFIED
    ver_resp = await client.patch(f"/api/v1/filings/{filing_id}", json={"status": "VERIFIED"}, headers=headers)
    assert ver_resp.status_code == 200
    
    # 5. Assert final state
    data = ver_resp.json()
    assert "id" in data
    assert data["status"] == "VERIFIED"


async def test_create_filing_unauthorized(client: AsyncClient):
    """
    Test Case: test_create_filing_unauthorized
    - POST without token
    - Expect 401
    """
    payload = {
        # Using a dummy taxpayer ID since it should be blocked before DB access
        "taxpayer_id": "00000000-0000-0000-0000-000000000000",
        "financial_year": "2023-24"
    }
    
    response = await client.post("/api/v1/filings", json=payload)
    
    assert response.status_code == 401
    assert "detail" in response.json()


async def test_filing_transition_unauthorized(client: AsyncClient):
    """
    Test Case: test_filing_transition_unauthorized
    - PATCH without token
    - Expect 401
    """
    # Dummy ID, route should block before verifying if filing exists
    response = await client.patch(
        "/api/v1/filings/00000000-0000-0000-0000-000000000000",
        json={"status": "READY"}
    )
    
    assert response.status_code == 401
    assert "detail" in response.json()
