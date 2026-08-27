import pytest
from uuid import uuid4
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_edit_delete_channel_lifecycle(client: AsyncClient, santiago_token: str):
    """
    Verifica el ciclo de vida completo de un canal: creación, edición y archivado/eliminación por un admin/owner.
    """
    ch_name = f"#qa-lifecycle-{uuid4().hex[:6]}"
    # 1. Create channel
    resp = await client.post(
        "/api/channels",
        headers={"Authorization": f"Bearer {santiago_token}"},
        json={
            "name": ch_name,
            "description": "Canal inicial de pruebas de ciclo de vida",
            "type": "public"
        }
    )
    assert resp.status_code == 201
    channel_id = resp.json()["id"]

    # 2. Edit channel
    updated_name = f"#qa-updated-{uuid4().hex[:6]}"
    edit_resp = await client.patch(
        f"/api/channels/{channel_id}",
        headers={"Authorization": f"Bearer {santiago_token}"},
        json={
            "name": updated_name,
            "description": "Descripción actualizada"
        }
    )
    assert edit_resp.status_code == 200

    # Verify update in list
    list_resp = await client.get("/api/channels", headers={"Authorization": f"Bearer {santiago_token}"})
    channels = list_resp.json()
    updated_item = [c for c in channels if c["channel_id"] == channel_id]
    assert len(updated_item) == 1
    assert updated_item[0]["channel_name"] == updated_name
    assert updated_item[0]["channel_description"] == "Descripción actualizada"

    # 3. Delete / archive channel
    del_resp = await client.delete(f"/api/channels/{channel_id}", headers={"Authorization": f"Bearer {santiago_token}"})
    assert del_resp.status_code == 200

    # Verify channel is no longer active in user list
    list_resp2 = await client.get("/api/channels", headers={"Authorization": f"Bearer {santiago_token}"})
    channels2 = list_resp2.json()
    active_item = [c for c in channels2 if c["channel_id"] == channel_id]
    assert len(active_item) == 0
