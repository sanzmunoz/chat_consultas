from typing import Optional
from uuid import UUID
from src.domain.ports.message_repository import MessageRepositoryPort
from src.domain.ports.llm_service import LlmServicePort

class SendMessageUseCase:
    def __init__(self, message_repo: MessageRepositoryPort, llm_service: LlmServicePort):
        self.message_repo = message_repo
        self.llm_service = llm_service

    async def execute(
        self,
        actor_id: UUID,
        channel_id: UUID,
        content: str,
        status: str = "sent",
        msg_ref: Optional[str] = None
    ) -> UUID:
        """
        Generates vector embedding for message content and invokes atomic
        database function rw_fn_send_message enforcing channel membership and RLS.
        """
        # Generate 1536-dim embedding for RAG retrieval
        embedding = None
        if content and status == "sent":
            try:
                embedding = await self.llm_service.generate_embedding(content)
            except Exception:
                embedding = None

        return await self.message_repo.send_message(
            actor_id=actor_id,
            channel_id=channel_id,
            content=content,
            embedding=embedding,
            status=status,
            msg_ref=msg_ref
        )
