import pytest
from httpx import AsyncClient

GENERAL_CHANNEL_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"

@pytest.mark.asyncio
async def test_message_send_edit_delete_lifecycle(client: AsyncClient, santiago_token: str):
    """
    Verifies full lifecycle of messages:
    - Send atomic message
    - Keyset pagination retrieval
    - Edit with original_content preservation
    - Logical soft deletion
    """
    # 1. Send message
    send_resp = await client.post(
        f"/api/channels/{GENERAL_CHANNEL_ID}/messages",
        headers={"Authorization": f"Bearer {santiago_token}"},
        json={
            "content": "Mensaje para ciclo de vida completo",
            "status": "sent"
        }
    )
    assert send_resp.status_code == 201, f"Error: {send_resp.text}"
    msg_data = send_resp.json()
    msg_id = msg_data["id"]
    assert msg_id is not None

    # 2. Keyset pagination fetch
    list_resp = await client.get(
        f"/api/channels/{GENERAL_CHANNEL_ID}/messages?limit=5",
        headers={"Authorization": f"Bearer {santiago_token}"}
    )
    assert list_resp.status_code == 200
    msgs = list_resp.json()["messages"]
    assert any(m["id"] == msg_id for m in msgs)

    # 3. Edit message
    edit_resp = await client.patch(
        f"/api/messages/{msg_id}",
        headers={"Authorization": f"Bearer {santiago_token}"},
        json={"content": "Mensaje editado en el ciclo de vida"}
    )
    assert edit_resp.status_code == 200

    # Verify edit preserved original content
    verify_list = await client.get(
        f"/api/channels/{GENERAL_CHANNEL_ID}/messages?limit=5",
        headers={"Authorization": f"Bearer {santiago_token}"}
    )
    edited_msg = next(m for m in verify_list.json()["messages"] if m["id"] == msg_id)
    assert edited_msg["is_edited"] is True
    assert edited_msg["original_content"] == "Mensaje para ciclo de vida completo"
    assert edited_msg["content"] == "Mensaje editado en el ciclo de vida"

    # 4. Soft delete message
    del_resp = await client.delete(
        f"/api/messages/{msg_id}",
        headers={"Authorization": f"Bearer {santiago_token}"}
    )
    assert del_resp.status_code == 200

    # Verify soft deleted message is no longer returned in active listing
    after_del_list = await client.get(
        f"/api/channels/{GENERAL_CHANNEL_ID}/messages?limit=10",
        headers={"Authorization": f"Bearer {santiago_token}"}
    )
    assert not any(m["id"] == msg_id for m in after_del_list.json()["messages"])
