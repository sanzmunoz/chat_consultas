from typing import Optional, List
from uuid import UUID
from src.domain.entities.channel import Channel
from src.domain.ports.channel_repository import ChannelRepositoryPort

class CreateChannelUseCase:
    def __init__(self, channel_repo: ChannelRepositoryPort):
        self.channel_repo = channel_repo

    async def execute(
        self,
        actor_id: UUID,
        name: str,
        description: Optional[str] = None,
        type: str = "public",
        member_ids: Optional[List[UUID]] = None
    ) -> Channel:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Channel name cannot be empty.")
        if type not in ("public", "private"):
            raise ValueError("Channel type must be either 'public' or 'private'.")

        return await self.channel_repo.create_channel(
            actor_id=actor_id,
            name=clean_name,
            description=description.strip() if description else None,
            type=type,
            member_ids=member_ids
        )
