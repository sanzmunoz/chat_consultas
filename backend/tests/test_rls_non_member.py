import pytest
from httpx import AsyncClient

# Channel IDs
FRONTEND_CHANNEL_ID = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"  # Members: Camila, Valentina. NOT Nestor.
BACKEND_CHANNEL_ID  = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"  # Members: Santiago, Nestor. NOT Camila.

@pytest.mark.asyncio
async def test_non_member_cannot_read_messages(client: AsyncClient, nestor_token: str, camila_token: str):
    """
    Test 1 (Obligatorio): Verifica que un usuario NO miembro de un canal
    no puede ver sus mensajes (RLS rechaza o retorna lista vacía).
    """
    # 1. Nestor attempts to read messages from #frontend-design (where he is NOT a member)
    resp_nestor = await client.get(
        f"/api/channels/{FRONTEND_CHANNEL_ID}/messages",
        headers={"Authorization": f"Bearer {nestor_token}"}
    )
    assert resp_nestor.status_code == 200
    data_nestor = resp_nestor.json()
    assert len(data_nestor["messages"]) == 0, (
        f"Fallo de seguridad RLS: Néstor pudo ver {len(data_nestor['messages'])} mensajes de #frontend-design!"
    )

    # 2. Camila (who IS a member of #frontend-design) reads messages from #frontend-design
    resp_camila = await client.get(
        f"/api/channels/{FRONTEND_CHANNEL_ID}/messages",
        headers={"Authorization": f"Bearer {camila_token}"}
    )
    assert resp_camila.status_code == 200
    data_camila = resp_camila.json()
    assert len(data_camila["messages"]) > 0, "Camila debería poder ver los mensajes de su canal #frontend-design"

@pytest.mark.asyncio
async def test_non_member_cannot_send_messages(client: AsyncClient, nestor_token: str):
    """
    Verifica que un usuario NO miembro es rechazado al intentar enviar
    un mensaje a un canal privado ajeno.
    """
    resp = await client.post(
        f"/api/channels/{FRONTEND_CHANNEL_ID}/messages",
        headers={"Authorization": f"Bearer {nestor_token}"},
        json={"content": "Intento de intrusión no autorizado en #frontend-design"}
    )
    # Debe ser rechazado por la función atómica / RLS
    assert resp.status_code in (400, 403), f"Esperado rechazo pero se obtuvo {resp.status_code}: {resp.text}"
