from typing import List, Optional
from uuid import UUID
from datetime import datetime
from src.domain.entities.message import Message
from src.domain.ports.message_repository import MessageRepositoryPort

class ListMessagesKeysetUseCase:
    def __init__(self, message_repo: MessageRepositoryPort):
        self.message_repo = message_repo

    async def execute(
        self,
        actor_id: UUID,
        channel_id: UUID,
        cursor_created_at: Optional[datetime] = None,
        cursor_id: Optional[UUID] = None,
        limit: int = 20
    ) -> List[Message]:
        """
        Retrieves paginated messages using index-backed keyset pagination (O(1)).
        Prohibits OFFSET pagination to maintain stable scroll position.
        """
        return await self.message_repo.list_channel_messages_keyset(
            actor_id=actor_id,
            channel_id=channel_id,
            cursor_created_at=cursor_created_at,
            cursor_id=cursor_id,
            limit=limit
        )
