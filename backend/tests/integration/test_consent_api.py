import pytest
from httpx import AsyncClient
from uuid import uuid4

pytestmark = pytest.mark.asyncio

# Global counter to keep email, mobile and PAN unique across test cases
_counter = 0

async def create_user_and_login(client: AsyncClient, email: str, role: str) -> str:
    """Helper to register and login a user, returning their access token."""
    global _counter
    _counter += 1
    
    # Build unique, valid PAN: 5 letters, 4 digits, 1 letter
    # 4th char is 'P' for Individual/CA, 'C' for Business
    p4 = "C" if role == "BUSINESS" else "P"
    pan = f"ABCE{p4}{1000 + _counter:04d}Z"
    
    reg_payload = {
        "email": email,
        "password": "StrongPassword123!",
        "legal_name": f"{role} User {_counter}",
        "mobile": f"987654{1000 + _counter:04d}",
        "pan": pan,
        "primary_role": role
    }
    reg_resp = await client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_resp.status_code == 201, f"Registration failed: {reg_resp.text}"
    
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "StrongPassword123!"}
    )
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    return login_resp.json()["access_token"]


async def test_consent_list_empty(client: AsyncClient):
    """
    Test GET /api/v1/consent/
    - Should return 200 OK and an empty list when no consents are granted.
    """
    token = await create_user_and_login(client, "taxpayer_empty@example.com", "INDIVIDUAL")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await client.get("/api/v1/consent/", headers=headers)
    assert response.status_code == 200
    assert response.json() == []


async def test_consent_grant_and_list(client: AsyncClient):
    """
    Test grant and then GET /api/v1/consent/
    - Should return the granted consent in the list.
    """
    token = await create_user_and_login(client, "taxpayer_grant@example.com", "INDIVIDUAL")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Grant consent
    grant_payload = {
        "purpose": "Review ledger",
        "scope": "FULL_ACCESS",
        "expiry_at": "2026-12-31T23:59:59Z"
    }
    grant_resp = await client.post("/api/v1/consent/", json=grant_payload, headers=headers)
    assert grant_resp.status_code == 201
    consent_id = grant_resp.json()["id"]
    
    # 2. List consents
    list_resp = await client.get("/api/v1/consent/", headers=headers)
    assert list_resp.status_code == 200
    consents = list_resp.json()
    assert len(consents) == 1
    assert consents[0]["id"] == consent_id
    assert consents[0]["purpose"] == "Review ledger"
    assert consents[0]["scope"] == "FULL_ACCESS"


async def test_consent_get_by_id_and_ownership(client: AsyncClient):
    """
    Test GET /api/v1/consent/{consent_id}
    - Should return 200 OK for owner.
    - Should return 404 for a different taxpayer (prevent ID scanning).
    """
    token1 = await create_user_and_login(client, "taxpayer1@example.com", "INDIVIDUAL")
    token2 = await create_user_and_login(client, "taxpayer2@example.com", "INDIVIDUAL")
    
    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}
    
    # 1. Taxpayer 1 grants consent
    grant_payload = {
        "purpose": "Review ledger",
        "scope": "FULL_ACCESS",
        "expiry_at": "2026-12-31T23:59:59Z"
    }
    grant_resp = await client.post("/api/v1/consent/", json=grant_payload, headers=headers1)
    assert grant_resp.status_code == 201
    consent_id = grant_resp.json()["id"]
    
    # 2. Taxpayer 1 fetches their own consent
    get_resp = await client.get(f"/api/v1/consent/{consent_id}", headers=headers1)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == consent_id
    
    # 3. Taxpayer 2 attempts to fetch Taxpayer 1's consent (Should get 404)
    get_unauth_resp = await client.get(f"/api/v1/consent/{consent_id}", headers=headers2)
    assert get_unauth_resp.status_code == 404


async def test_consent_get_not_found(client: AsyncClient):
    """
    Test GET /api/v1/consent/{consent_id} with a non-existent UUID.
    - Should return 404.
    """
    token = await create_user_and_login(client, "taxpayer_nf@example.com", "INDIVIDUAL")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await client.get(f"/api/v1/consent/{uuid4()}", headers=headers)
    assert response.status_code == 404


async def test_consent_access_control(client: AsyncClient):
    """
    Test that unauthorized roles (like CAs) cannot list or grant consents.
    """
    ca_token = await create_user_and_login(client, "ca_access@example.com", "CA")
    headers = {"Authorization": f"Bearer {ca_token}"}
    
    # CAs cannot access taxpayer consent endpoints
    list_resp = await client.get("/api/v1/consent/", headers=headers)
    assert list_resp.status_code == 403
    
    # No auth token at all
    no_auth_resp = await client.get("/api/v1/consent/")
    assert no_auth_resp.status_code == 401


async def test_ca_discovery_api(client: AsyncClient):
    """
    Test GET /api/v1/auth/cas
    - Taxpayers can discover active CAs.
    - Safe public fields only are returned.
    - CAs themselves cannot access it (returns 403).
    """
    taxpayer_token = await create_user_and_login(client, "taxpayer_discover@example.com", "INDIVIDUAL")
    ca_token = await create_user_and_login(client, "ca_discover@example.com", "CA")
    
    headers_tp = {"Authorization": f"Bearer {taxpayer_token}"}
    headers_ca = {"Authorization": f"Bearer {ca_token}"}
    
    # 1. Taxpayer discovers CAs
    discovery_resp = await client.get("/api/v1/auth/cas", headers=headers_tp)
    assert discovery_resp.status_code == 200
    cas = discovery_resp.json()
    assert len(cas) >= 1
    
    # Check that our created CA is in the list and only safe fields are returned
    ca_item = next((c for c in cas if c["email"] == "ca_discover@example.com"), None)
    assert ca_item is not None
    assert "id" in ca_item
    assert "CA User" in ca_item["legal_name"]
    assert "password" not in ca_item
    assert "password_hash" not in ca_item
    
    # 2. CA attempts to discover CAs (Should get 403 Forbidden)
    ca_unauth_resp = await client.get("/api/v1/auth/cas", headers=headers_ca)
    assert ca_unauth_resp.status_code == 403
