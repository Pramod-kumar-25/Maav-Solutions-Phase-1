import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def _get_auth_token(client: AsyncClient, email: str = "taxpayer@example.com") -> str:
    """Helper to register and login a user to get a token."""
    password = "StrongPassword123!"
    
    # Register
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Test Taxpayer",
            "primary_role": "INDIVIDUAL"
        }
    )
    
    # Login
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password}
    )
    return response.json()["access_token"]


async def test_create_taxpayer_profile_success(client: AsyncClient):
    """
    Test Case: test_create_taxpayer_profile_success
    - Authenticated user creates profile
    - Expect 200 response
    - Validate response structure
    """
    token = await _get_auth_token(client, "create_success@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "days_in_india_current_fy": 182,
        "days_in_india_last_4_years": 400,
        "has_foreign_income": False,
        "default_tax_regime": "NEW",
        "aadhaar_link_status": True
    }
    
    response = await client.post("/api/v1/taxpayer/profile", json=payload, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "user_id" in data
    assert data["days_in_india_current_fy"] == 182
    assert "residential_status" in data
    assert data["default_tax_regime"] == "NEW"


async def test_create_taxpayer_profile_unauthorized(client: AsyncClient):
    """
    Test Case: test_create_taxpayer_profile_unauthorized
    - No token provided
    - Expect 401
    """
    payload = {
        "days_in_india_current_fy": 182,
        "days_in_india_last_4_years": 400,
        "has_foreign_income": False,
        "default_tax_regime": "NEW",
        "aadhaar_link_status": True
    }
    
    response = await client.post("/api/v1/taxpayer/profile", json=payload)
    
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data


async def test_get_taxpayer_profile(client: AsyncClient):
    """
    Test Case: test_get_taxpayer_profile
    - Fetch profile for authenticated user
    - Validate returned data
    """
    token = await _get_auth_token(client, "get_profile@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "days_in_india_current_fy": 200,
        "days_in_india_last_4_years": 800,
        "has_foreign_income": True,
        "default_tax_regime": "OLD",
        "aadhaar_link_status": True
    }
    
    # 1. Create the profile
    create_resp = await client.post("/api/v1/taxpayer/profile", json=payload, headers=headers)
    assert create_resp.status_code == 200
    
    # 2. Fetch the profile
    response = await client.get("/api/v1/taxpayer/profile", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["days_in_india_current_fy"] == 200
    assert data["has_foreign_income"] is True
    assert "residential_status" in data
    assert data["default_tax_regime"] == "OLD"


async def test_duplicate_taxpayer_profile(client: AsyncClient):
    """
    Test Case: test_duplicate_taxpayer_profile
    - Attempt to create profile again
    - Expect error response
    """
    token = await _get_auth_token(client, "duplicate_profile@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "days_in_india_current_fy": 182,
        "days_in_india_last_4_years": 400,
        "has_foreign_income": False,
        "default_tax_regime": "NEW",
        "aadhaar_link_status": True
    }
    
    # 1. Create the profile successfully
    first_resp = await client.post("/api/v1/taxpayer/profile", json=payload, headers=headers)
    assert first_resp.status_code == 200
    
    # 2. Attempt duplicate creation
    second_resp = await client.post("/api/v1/taxpayer/profile", json=payload, headers=headers)
    
    # We strictly enforce the 400 error schema validation for duplicates
    assert second_resp.status_code == 400
    data = second_resp.json()
    assert "detail" in data


async def test_get_taxpayer_profile_not_found(client: AsyncClient):
    """
    Test Case: test_get_taxpayer_profile_not_found
    - Call GET /api/v1/taxpayer/profile before profile creation
    - Expect 404 response
    - Validate error structure
    """
    token = await _get_auth_token(client, "not_found@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await client.get("/api/v1/taxpayer/profile", headers=headers)
    
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


async def test_get_taxpayer_profile_unauthorized(client: AsyncClient):
    """
    Test Case: test_get_taxpayer_profile_unauthorized
    - Call GET without token
    - Expect 401
    """
    response = await client.get("/api/v1/taxpayer/profile")
    
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
