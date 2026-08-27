from typing import Optional
from uuid import UUID
from src.domain.entities.copilot_log import CopilotTokenUsage
from src.domain.ports.copilot_log_repository import CopilotLogRepositoryPort

class GetCopilotUsageUseCase:
    def __init__(self, copilot_log_repo: CopilotLogRepositoryPort):
        self.copilot_log_repo = copilot_log_repo

    async def execute(self, user_id: UUID) -> Optional[CopilotTokenUsage]:
        """Retrieves accumulated copilot token metrics for user."""
        return await self.copilot_log_repo.get_user_token_usage(user_id)
