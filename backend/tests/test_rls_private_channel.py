import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_search_does_not_leak_private_channels(client: AsyncClient, camila_token: str, nestor_token: str):
    """
    Test 2 (Obligatorio): Confirmar que los mensajes de canales privados
    ajenos NO se retornan en búsquedas ni listados.
    """
    # 1. Camila searches for backend terms discussed in private channel #backend-dev (e.g. 'asyncpg' or 'pool')
    resp_camila = await client.get(
        "/api/messages/search?q=asyncpg",
        headers={"Authorization": f"Bearer {camila_token}"}
    )
    assert resp_camila.status_code == 200
    camila_results = resp_camila.json()
    
    # Verify no result comes from #backend-dev
    for item in camila_results:
        assert item["channel_name"] != "#backend-dev", (
            f"Fallo de aislamiento: Camila recibió mensaje del canal privado ajeno #backend-dev: {item['content']}"
        )

    # 2. Nestor searches for frontend terms discussed in private channel #frontend-design (e.g. 'mockups')
    resp_nestor = await client.get(
        "/api/messages/search?q=mockups",
        headers={"Authorization": f"Bearer {nestor_token}"}
    )
    assert resp_nestor.status_code == 200
    nestor_results = resp_nestor.json()

    # Verify no result comes from #frontend-design
    for item in nestor_results:
        assert item["channel_name"] != "#frontend-design", (
            f"Fallo de aislamiento: Néstor recibió mensaje del canal privado ajeno #frontend-design: {item['content']}"
        )
