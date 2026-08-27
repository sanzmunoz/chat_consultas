from uuid import UUID
from src.domain.ports.message_repository import MessageRepositoryPort

class EditMessageUseCase:
    def __init__(self, message_repo: MessageRepositoryPort):
        self.message_repo = message_repo

    async def execute(self, actor_id: UUID, message_id: UUID, new_content: str) -> bool:
        """
        Edits message preserving original_content in database audit trail.
        """
        if not new_content or not new_content.strip():
            raise ValueError("Message content cannot be empty.")
        return await self.message_repo.edit_message(actor_id, message_id, new_content.strip())
