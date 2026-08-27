from typing import Optional, List
from uuid import UUID
from datetime import datetime
from src.domain.entities.message import Message
from src.domain.ports.message_repository import MessageRepositoryPort
from src.infrastructure.database.pool import get_connection_with_actor

class PgMessageRepository(MessageRepositoryPort):

    async def send_message(
        self,
        actor_id: UUID,
        channel_id: UUID,
        content: str,
        embedding: Optional[List[float]] = None,
        status: str = "sent",
        msg_ref: Optional[str] = None
    ) -> UUID:
        async with get_connection_with_actor(actor_id) as conn:
            vec_str = None
            if embedding:
                vec_str = "[" + ",".join(str(x) for x in embedding[:1536]) + "]"
            
            # Execute atomic database function rw_fn_send_message
            if vec_str:
                msg_id = await conn.fetchval(
                    """
                    SELECT rw_fn_send_message($1, $2, $3::vector, $4, $5);
                    """,
                    channel_id, content, vec_str, status, msg_ref
                )
            else:
                msg_id = await conn.fetchval(
                    """
                    SELECT rw_fn_send_message($1, $2, NULL, $3, $4);
                    """,
                    channel_id, content, status, msg_ref
                )
            return msg_id

    async def list_channel_messages_keyset(
        self,
        actor_id: UUID,
        channel_id: UUID,
        cursor_created_at: Optional[datetime] = None,
        cursor_id: Optional[UUID] = None,
        limit: int = 20
    ) -> List[Message]:
        async with get_connection_with_actor(actor_id) as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    m.id,
                    m.msg_ref,
                    m.channel_id,
                    m.author_id,
                    u.display_name AS author_name,
                    u.username AS author_username,
                    u.position AS author_position,
                    m.content,
                    m.original_content,
                    m.status,
                    m.is_edited,
                    m.edited_at,
                    m.is_deleted,
                    m.created_at,
                    m.updated_at,
                    (
                        SELECT COUNT(rr.id) 
                        FROM rw_read_receipts rr 
                        WHERE rr.message_id = m.id
                    ) AS read_count,
                    EXISTS (
                        SELECT 1 
                        FROM rw_read_receipts rr 
                        WHERE rr.message_id = m.id 
                          AND rr.user_id = rw_get_current_user_id()
                    ) AS is_read_by_me
                FROM rw_messages m
                JOIN rw_users u ON m.author_id = u.id
                WHERE m.channel_id = $1
                  AND m.is_deleted = FALSE
                  AND rw_is_channel_member(m.channel_id)
                  AND (
                      $2::TIMESTAMPTZ IS NULL 
                      OR (m.created_at, m.id) < ($2, $3::UUID)
                  )
                ORDER BY m.created_at DESC, m.id DESC
                LIMIT LEAST(COALESCE($4, 20), 100);
                """,
                channel_id, cursor_created_at, cursor_id, limit
            )
            return [
                Message(
                    id=r["id"],
                    msg_ref=r["msg_ref"],
                    channel_id=r["channel_id"],
                    author_id=r["author_id"],
                    content=r["content"],
                    original_content=r["original_content"],
                    is_edited=r["is_edited"],
                    edited_at=r["edited_at"],
                    is_deleted=r["is_deleted"],
                    status=r["status"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                    author_name=r["author_name"],
                    author_username=r["author_username"],
                    author_position=r["author_position"],
                    read_count=r["read_count"],
                    is_read_by_me=r["is_read_by_me"]
                )
                for r in rows
            ]

    async def search_messages_highlight(
        self,
        actor_id: UUID,
        search_term: str,
        limit: int = 20
    ) -> List[Message]:
        async with get_connection_with_actor(actor_id) as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    m.id,
                    m.msg_ref,
                    m.channel_id,
                    c.name AS channel_name,
                    m.author_id,
                    u.display_name AS author_name,
                    u.username AS author_username,
                    u.position AS author_position,
                    m.content,
                    m.original_content,
                    m.is_edited,
                    m.status,
                    m.created_at,
                    ts_headline(
                        'spanish', 
                        m.content, 
                        websearch_to_tsquery('spanish', $1),
                        'StartSel = <mark>, StopSel = </mark>, MaxWords=40, MinWords=15, HighlightAll=FALSE'
                    ) AS highlighted_content,
                    ts_rank(m.search_vector, websearch_to_tsquery('spanish', $1)) AS search_rank
                FROM rw_messages m
                JOIN rw_channels c ON m.channel_id = c.id
                JOIN rw_users u ON m.author_id = u.id
                WHERE m.is_deleted = FALSE
                  AND rw_is_channel_member(m.channel_id)
                  AND m.search_vector @@ websearch_to_tsquery('spanish', $1)
                ORDER BY search_rank DESC, m.created_at DESC
                LIMIT LEAST(COALESCE($2, 20), 50);
                """,
                search_term, limit
            )
            return [
                Message(
                    id=r["id"],
                    msg_ref=r["msg_ref"],
                    channel_id=r["channel_id"],
                    author_id=r["author_id"],
                    content=r["content"],
                    original_content=r["original_content"],
                    is_edited=r["is_edited"],
                    status=r["status"],
                    created_at=r["created_at"],
                    author_name=r["author_name"],
                    author_username=r["author_username"],
                    author_position=r["author_position"],
                    highlighted_content=r["highlighted_content"],
                    search_rank=float(r["search_rank"]) if r["search_rank"] is not None else 0.0
                )
                for r in rows
            ]

    async def edit_message(
        self,
        actor_id: UUID,
        message_id: UUID,
        new_content: str
    ) -> bool:
        async with get_connection_with_actor(actor_id) as conn:
            return await conn.fetchval(
                """
                SELECT rw_fn_edit_message($1, $2);
                """,
                message_id, new_content
            )

    async def delete_message(
        self,
        actor_id: UUID,
        message_id: UUID
    ) -> bool:
        async with get_connection_with_actor(actor_id) as conn:
            return await conn.fetchval(
                """
                SELECT rw_fn_delete_message($1);
                """,
                message_id
            )

    async def retrieve_copilot_context_embeddings(
        self,
        actor_id: UUID,
        query_embedding: List[float],
        similarity_threshold: float = 0.70,
        limit: int = 5
    ) -> List[Message]:
        async with get_connection_with_actor(actor_id) as conn:
            vec_str = "[" + ",".join(str(x) for x in query_embedding[:1536]) + "]"
            rows = await conn.fetch(
                f"""
                SELECT 
                    m.id,
                    m.msg_ref,
                    m.channel_id,
                    c.name AS channel_name,
                    m.author_id,
                    u.display_name AS author_name,
                    u.username AS author_username,
                    u.position AS author_position,
                    m.content,
                    m.created_at,
                    (1 - (m.embedding <=> '{vec_str}'::vector)) AS similarity_score
                FROM rw_messages m
                JOIN rw_channels c ON m.channel_id = c.id
                JOIN rw_users u ON m.author_id = u.id
                WHERE m.is_deleted = FALSE
                  AND m.embedding IS NOT NULL
                  AND rw_is_channel_member(m.channel_id)
                ORDER BY m.embedding <=> '{vec_str}'::vector ASC
                LIMIT LEAST(COALESCE($1, 5), 20);
                """,
                limit
            )
            return [
                Message(
                    id=r["id"],
                    msg_ref=r["msg_ref"],
                    channel_id=r["channel_id"],
                    author_id=r["author_id"],
                    content=r["content"],
                    created_at=r["created_at"],
                    author_name=r["author_name"],
                    author_username=r["author_username"],
                    author_position=f"{r['channel_name']} | {r['author_position']}",
                    search_rank=float(r["similarity_score"]) if r["similarity_score"] is not None else 0.0
                )
                for r in rows
            ]
