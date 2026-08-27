from uuid import UUID
from src.domain.ports.message_repository import MessageRepositoryPort

class DeleteMessageUseCase:
    def __init__(self, message_repo: MessageRepositoryPort):
        self.message_repo = message_repo

    async def execute(self, actor_id: UUID, message_id: UUID) -> bool:
        """
        Performs logical soft-delete of message (is_deleted = TRUE).
        Physical deletion is strictly prohibited.
        """
        return await self.message_repo.delete_message(actor_id, message_id)
