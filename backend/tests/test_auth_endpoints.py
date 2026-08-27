import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_auth_login_and_me(client: AsyncClient):
    """Verifies login generates valid token and /me endpoint retrieves claims."""
    # Successful login
    resp = await client.post("/api/auth/login", json={
        "username_or_email": "smunoz",
        "password": "riwi2026!"
    })
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["user"]["username"] == "smunoz"
    assert body["user"]["role"] == "admin"

    # Access /api/auth/me
    token = body["access_token"]
    me_resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["username"] == "smunoz"
    assert me_data["email"] == "santiago.munoz@riwi.co"

@pytest.mark.asyncio
async def test_refresh_token_rotation(client: AsyncClient):
    """Verifies refresh token rotation (single-use semantics)."""
    # 1. Login to get refresh token
    login_resp = await client.post("/api/auth/login", json={
        "username_or_email": "crojas",
        "password": "riwi2026!"
    })
    assert login_resp.status_code == 200
    refresh_tok_1 = login_resp.json()["refresh_token"]

    # 2. Use refresh token once (should succeed)
    rot_resp_1 = await client.post("/api/auth/refresh", json={
        "refresh_token": refresh_tok_1
    })
    assert rot_resp_1.status_code == 200
    body_rot_1 = rot_resp_1.json()
    refresh_tok_2 = body_rot_1["refresh_token"]
    assert refresh_tok_2 != refresh_tok_1

    # 3. Attempt to REUSE the previous refresh token (must be REJECTED)
    rot_resp_reuse = await client.post("/api/auth/refresh", json={
        "refresh_token": refresh_tok_1
    })
    assert rot_resp_reuse.status_code == 401, "El refresh token antiguo debería estar revocado y rechazado"
