from typing import Protocol, Optional
from uuid import UUID
from src.domain.entities.copilot_log import CopilotTokenUsage

class CopilotLogRepositoryPort(Protocol):
    async def log_copilot_interaction(
        self,
        user_id: UUID,
        query: str,
        response: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        model: str,
        prompt_version: str
    ) -> UUID:
        ...

    async def get_user_token_usage(self, user_id: UUID) -> Optional[CopilotTokenUsage]:
        ...
