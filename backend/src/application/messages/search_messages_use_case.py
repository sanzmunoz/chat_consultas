from typing import List
from uuid import UUID
from src.domain.entities.message import Message
from src.domain.ports.message_repository import MessageRepositoryPort

class SearchMessagesUseCase:
    def __init__(self, message_repo: MessageRepositoryPort):
        self.message_repo = message_repo

    async def execute(
        self,
        actor_id: UUID,
        search_term: str,
        limit: int = 20
    ) -> List[Message]:
        """
        Executes full-text search with term highlighting (ts_headline)
        strictly scoped to channels where actor is a member.
        """
        if not search_term or not search_term.strip():
            return []
        return await self.message_repo.search_messages_highlight(
            actor_id=actor_id,
            search_term=search_term.strip(),
            limit=limit
        )
