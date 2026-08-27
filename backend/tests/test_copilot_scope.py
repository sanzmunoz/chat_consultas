import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_copilot_strictly_scopes_context(client: AsyncClient, valentina_token: str, santiago_token: str):
    """
    Test 3 (Obligatorio): El Copiloto RAG no recupera embeddings ni cita mensajes
    de canales donde el usuario autenticado no es miembro.
    """
    # 1. Valentina queries about backend internal topics from #backend-dev
    resp_valentina = await client.post(
        "/api/copilot/query",
        headers={"Authorization": f"Bearer {valentina_token}"},
        json={"query": "¿Qué se ha discutido sobre las políticas RLS en el canal de backend?"}
    )
    assert resp_valentina.status_code == 200, f"Error: {resp_valentina.text}"
    val_data = resp_valentina.json()

    # Assert Valentina receives NO citations from #backend-dev
    for citation in val_data["citations"]:
        assert citation["channel_name"] != "#backend-dev", (
            f"Fallo de seguridad Copiloto: Valentina recibió cita de canal ajeno: {citation}"
        )

    # 2. Santiago (who IS a member of #backend-dev) queries the same topic
    resp_santiago = await client.post(
        "/api/copilot/query",
        headers={"Authorization": f"Bearer {santiago_token}"},
        json={"query": "¿Qué bloqueos tiene el equipo backend?"}
    )
    assert resp_santiago.status_code == 200
    sant_data = resp_santiago.json()
    assert sant_data["response"] is not None
    assert sant_data["prompt_tokens"] > 0
    assert len(sant_data["citations"]) > 0

    # 3. Valentina queries about DevOps/Render (a private channel she does NOT belong to)
    resp_val_devops = await client.post(
        "/api/copilot/query",
        headers={"Authorization": f"Bearer {valentina_token}"},
        json={"query": "¿Cuál es el estado del deploy en Render?"}
    )
    assert resp_val_devops.status_code == 200
    val_devops_data = resp_val_devops.json()
    assert len(val_devops_data["citations"]) == 0
    assert "No tengo acceso a los mensajes de los canales relacionados" in val_devops_data["response"]
