from typing import List
from uuid import UUID
from src.domain.entities.channel import ChannelConversationSummary
from src.domain.ports.channel_repository import ChannelRepositoryPort

class ListUserChannelsUseCase:
    def __init__(self, channel_repo: ChannelRepositoryPort):
        self.channel_repo = channel_repo

    async def execute(self, user_id: UUID) -> List[ChannelConversationSummary]:
        """Lists active channels for user with unread counts and last message."""
        return await self.channel_repo.list_user_conversations(user_id)
