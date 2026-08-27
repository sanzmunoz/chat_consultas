from typing import List, Dict, Any
from uuid import UUID
from src.domain.ports.channel_repository import ChannelRepositoryPort

class GetChannelMembersUseCase:
    def __init__(self, channel_repo: ChannelRepositoryPort):
        self.channel_repo = channel_repo

    async def execute(self, channel_id: UUID, user_id: UUID) -> List[Dict[str, Any]]:
        """Retrieves list of active members in a channel."""
        return await self.channel_repo.get_channel_members(channel_id, user_id)
