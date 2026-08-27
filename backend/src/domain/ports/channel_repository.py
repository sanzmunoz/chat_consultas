from typing import Protocol, Optional, List, Dict, Any
from uuid import UUID
from src.domain.entities.channel import Channel, ChannelConversationSummary

class ChannelRepositoryPort(Protocol):
    async def list_user_conversations(self, user_id: UUID) -> List[ChannelConversationSummary]:
        ...

    async def get_channel_by_id(self, channel_id: UUID, user_id: UUID) -> Optional[Channel]:
        ...

    async def get_channel_members(self, channel_id: UUID, user_id: UUID) -> List[Dict[str, Any]]:
        ...

    async def is_member(self, channel_id: UUID, user_id: UUID) -> bool:
        ...
