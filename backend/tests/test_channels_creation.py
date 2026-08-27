import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_channel_endpoint(client: AsyncClient, santiago_token: str):
    """
    Verifica que el endpoint POST /api/channels crea un nuevo canal
    y lo retorna con rol 'owner' en la lista de conversaciones.
    """
    resp = await client.post(
        "/api/channels",
        headers={"Authorization": f"Bearer {santiago_token}"},
        json={
            "name": "#qa-automation-testing",
            "description": "Canal de pruebas de automatización QA",
            "type": "public"
        }
    )
    assert resp.status_code == 201, f"Error: {resp.text}"
    data = resp.json()
    assert data["name"] == "#qa-automation-testing"
    assert data["type"] == "public"
    assert data["created_by"] is not None

    # Check that it appears in user channels
    list_resp = await client.get(
        "/api/channels",
        headers={"Authorization": f"Bearer {santiago_token}"}
    )
    assert list_resp.status_code == 200
    channels = list_resp.json()
    created = [c for c in channels if c["channel_name"] == "#qa-automation-testing"]
    assert len(created) == 1
    assert created[0]["user_channel_role"] == "owner"
