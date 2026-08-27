from typing import Protocol, Optional, List
from uuid import UUID
from datetime import datetime
from src.domain.entities.message import Message

class MessageRepositoryPort(Protocol):
    async def send_message(
        self,
        actor_id: UUID,
        channel_id: UUID,
        content: str,
        embedding: Optional[List[float]] = None,
        status: str = "sent",
        msg_ref: Optional[str] = None
    ) -> UUID:
        ...

    async def list_channel_messages_keyset(
        self,
        actor_id: UUID,
        channel_id: UUID,
        cursor_created_at: Optional[datetime] = None,
        cursor_id: Optional[UUID] = None,
        limit: int = 20
    ) -> List[Message]:
        ...

    async def search_messages_highlight(
        self,
        actor_id: UUID,
        search_term: str,
        limit: int = 20
    ) -> List[Message]:
        ...

    async def edit_message(
        self,
        actor_id: UUID,
        message_id: UUID,
        new_content: str
    ) -> bool:
        ...

    async def delete_message(
        self,
        actor_id: UUID,
        message_id: UUID
    ) -> bool:
        ...

    async def retrieve_copilot_context_embeddings(
        self,
        actor_id: UUID,
        query_embedding: List[float],
        similarity_threshold: float = 0.70,
        limit: int = 5
    ) -> List[Message]:
        ...
