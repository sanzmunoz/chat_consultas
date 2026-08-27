import pytest
from httpx import AsyncClient

VALENTINA_USER_ID = "44444444-4444-4444-8444-444444444444"

@pytest.mark.asyncio
async def test_query_users_stored_procedure(client: AsyncClient, santiago_token: str):
    """Verifies rw_sp_query_users returns users with counts and filters."""
    resp = await client.get(
        "/api/users?search=Valentina",
        headers={"Authorization": f"Bearer {santiago_token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["users"]) == 1
    user = data["users"][0]
    assert user["username"] == "vcastro"
    assert user["channels_count"] >= 1

@pytest.mark.asyncio
async def test_edit_user_profile(client: AsyncClient, valentina_token: str):
    """Verifies user can edit own profile."""
    edit_resp = await client.patch(
        f"/api/users/{VALENTINA_USER_ID}",
        headers={"Authorization": f"Bearer {valentina_token}"},
        json={
            "display_name": "Valentina Castro Lead QA",
            "position": "Lead QA Engineer"
        }
    )
    assert edit_resp.status_code == 200
    assert edit_resp.json()["success"] is True
