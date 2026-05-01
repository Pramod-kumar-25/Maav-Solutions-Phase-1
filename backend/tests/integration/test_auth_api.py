import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_register_user_success(client: AsyncClient):
    """
    Test Case: test_register_user_success
    - Valid user registration
    - Expect 201 response
    - Validate response structure
    """
    payload = {
        "email": "newuser@example.com",
        "password": "StrongPassword123!",
        "full_name": "New User",
        "primary_role": "INDIVIDUAL"
    }

    response = await client.post("/api/v1/auth/register", json=payload)
    
    assert response.status_code == 201
    
    data = response.json()
    assert "id" in data
    assert data["email"] == payload["email"]
    assert "password" not in data
    assert "hashed_password" not in data


async def test_register_duplicate_user(client: AsyncClient):
    """
    Test Case: test_register_duplicate_user
    - Attempt duplicate registration
    - Expect error response
    """
    payload = {
        "email": "duplicate@example.com",
        "password": "StrongPassword123!",
        "full_name": "Duplicate User",
        "primary_role": "INDIVIDUAL"
    }

    # 1. Register successfully
    await client.post("/api/v1/auth/register", json=payload)

    # 2. Attempt duplicate registration
    response = await client.post("/api/v1/auth/register", json=payload)
    
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


async def test_login_success(client: AsyncClient):
    """
    Test Case: test_login_success
    - Valid credentials
    - Expect access token
    """
    email = "login_success@example.com"
    password = "StrongPassword123!"
    
    # 1. Register user
    await client.post(
        "/api/v1/auth/register", 
        json={
            "email": email, 
            "password": password, 
            "full_name": "Login User", 
            "primary_role": "INDIVIDUAL"
        }
    )

    # 2. Login using OAuth2 form data
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_login_invalid_credentials(client: AsyncClient):
    """
    Test Case: test_login_invalid_credentials
    - Invalid password
    - Expect 401
    """
    email = "invalid_login@example.com"
    password = "StrongPassword123!"
    
    # 1. Register user
    await client.post(
        "/api/v1/auth/register", 
        json={
            "email": email, 
            "password": password, 
            "full_name": "Invalid Login User", 
            "primary_role": "INDIVIDUAL"
        }
    )

    # 2. Attempt login with wrong password
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "WrongPassword123!"}
    )

    assert response.status_code == 401
    data = response.json()
    assert "detail" in data


async def test_protected_route_without_token(client: AsyncClient):
    """
    Test Case: test_protected_route_without_token
    - Call protected endpoint without token
    - Expect 401 Unauthorized
    """
    response = await client.post(
        "/api/v1/taxpayer/profile",
        json={"days_in_india_current_fy": 182}
    )

    assert response.status_code == 401
    data = response.json()
    assert "detail" in data


async def test_protected_route_with_token(client: AsyncClient):
    """
    Test Case: test_protected_route_with_token
    - Register user
    - Login to get access token
    - Call protected endpoint with Authorization header
    - Expect successful response (200)
    """
    email = "protected_access@example.com"
    password = "StrongPassword123!"
    
    # 1. Register user
    await client.post(
        "/api/v1/auth/register", 
        json={
            "email": email, 
            "password": password, 
            "full_name": "Protected Route User", 
            "primary_role": "INDIVIDUAL"
        }
    )

    # 2. Login to get token
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password}
    )
    token = login_resp.json()["access_token"]
    
    # 3. Access protected route
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.post(
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
    
    assert response.status_code == 200
