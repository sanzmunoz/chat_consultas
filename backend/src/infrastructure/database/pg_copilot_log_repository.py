from typing import Optional
from uuid import UUID
from src.domain.entities.copilot_log import CopilotTokenUsage
from src.domain.ports.copilot_log_repository import CopilotLogRepositoryPort
from src.infrastructure.database.pool import get_connection_with_actor

class PgCopilotLogRepository(CopilotLogRepositoryPort):

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
        async with get_connection_with_actor(user_id) as conn:
            return await conn.fetchval(
                """
                INSERT INTO rw_copilot_logs (
                    user_id, query, response, prompt_tokens, completion_tokens, total_tokens, model, prompt_version
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id;
                """,
                user_id, query, response, prompt_tokens, completion_tokens, total_tokens, model, prompt_version
            )

    async def get_user_token_usage(self, user_id: UUID) -> Optional[CopilotTokenUsage]:
        async with get_connection_with_actor(user_id) as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    u.id AS user_id,
                    u.display_name,
                    u.email,
                    COUNT(l.id) AS total_queries,
                    COALESCE(SUM(l.prompt_tokens), 0)::BIGINT AS total_prompt_tokens,
                    COALESCE(SUM(l.completion_tokens), 0)::BIGINT AS total_completion_tokens,
                    COALESCE(SUM(l.total_tokens), 0)::BIGINT AS total_tokens_used,
                    MAX(l.created_at) AS last_query_at
                FROM rw_users u
                LEFT JOIN rw_copilot_logs l ON u.id = l.user_id
                WHERE u.id = $1
                GROUP BY u.id, u.display_name, u.email;
                """,
                user_id
            )
            if not row:
                return None
            return CopilotTokenUsage(
                user_id=row["user_id"],
                display_name=row["display_name"],
                email=row["email"],
                total_queries=row["total_queries"],
                total_prompt_tokens=row["total_prompt_tokens"],
                total_completion_tokens=row["total_completion_tokens"],
                total_tokens_used=row["total_tokens_used"],
                last_query_at=row["last_query_at"]
            )
