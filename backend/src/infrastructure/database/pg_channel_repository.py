from typing import Optional, List, Dict, Any
from uuid import UUID
from src.domain.entities.channel import Channel, ChannelConversationSummary
from src.domain.ports.channel_repository import ChannelRepositoryPort
from src.infrastructure.database.pool import get_connection_with_actor

class PgChannelRepository(ChannelRepositoryPort):

    async def list_user_conversations(self, user_id: UUID) -> List[ChannelConversationSummary]:
        async with get_connection_with_actor(user_id) as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    channel_id,
                    channel_name,
                    channel_description,
                    channel_type,
                    is_archived,
                    user_channel_role,
                    member_count,
                    unread_count,
                    last_message_id,
                    last_message_content,
                    last_message_created_at,
                    last_message_author_name
                FROM rw_v_user_conversations
                ORDER BY COALESCE(last_message_created_at, joined_at) DESC;
                """
            )
            return [
                ChannelConversationSummary(
                    channel_id=r["channel_id"],
                    channel_name=r["channel_name"],
                    channel_description=r["channel_description"],
                    channel_type=r["channel_type"],
                    is_archived=r["is_archived"],
                    user_channel_role=r["user_channel_role"],
                    member_count=r["member_count"],
                    unread_count=r["unread_count"],
                    last_message_id=r["last_message_id"],
                    last_message_content=r["last_message_content"],
                    last_message_created_at=r["last_message_created_at"],
                    last_message_author_name=r["last_message_author_name"]
                )
                for r in rows
            ]

    async def get_channel_by_id(self, channel_id: UUID, user_id: UUID) -> Optional[Channel]:
        async with get_connection_with_actor(user_id) as conn:
            row = await conn.fetchrow(
                """
                SELECT id, name, description, type, created_by, is_archived, created_at, updated_at
                FROM rw_channels
                WHERE id = $1;
                """,
                channel_id
            )
            if not row:
                return None
            return Channel(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                type=row["type"],
                created_by=row["created_by"],
                is_archived=row["is_archived"],
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )

    async def get_channel_members(self, channel_id: UUID, user_id: UUID) -> List[Dict[str, Any]]:
        async with get_connection_with_actor(user_id) as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    cm.id,
                    cm.channel_id,
                    cm.user_id,
                    u.display_name,
                    u.username,
                    u.email,
                    u.position,
                    cm.role AS channel_role,
                    cm.joined_at
                FROM rw_channel_members cm
                JOIN rw_users u ON cm.user_id = u.id
                WHERE cm.channel_id = $1 AND u.is_active = TRUE
                ORDER BY cm.role DESC, u.display_name ASC;
                """,
                channel_id
            )
            return [
                {
                    "membership_id": r["id"],
                    "user_id": r["user_id"],
                    "display_name": r["display_name"],
                    "username": r["username"],
                    "email": r["email"],
                    "position": r["position"],
                    "role": r["channel_role"],
                    "joined_at": r["joined_at"]
                }
                for r in rows
            ]

    async def is_member(self, channel_id: UUID, user_id: UUID) -> bool:
        async with get_connection_with_actor(user_id) as conn:
            return await conn.fetchval(
                """
                SELECT rw_is_channel_member($1);
                """,
                channel_id
            )

    async def create_channel(
        self,
        actor_id: UUID,
        name: str,
        description: Optional[str] = None,
        type: str = "public",
        member_ids: Optional[List[UUID]] = None
    ) -> Channel:
        clean_name = name.strip()
        if not clean_name.startswith("#"):
            clean_name = f"#{clean_name}"

        async with get_connection_with_actor(actor_id) as conn:
            # 1. Insert channel
            row = await conn.fetchrow(
                """
                INSERT INTO rw_channels (name, description, type, created_by)
                VALUES ($1, $2, $3, $4)
                RETURNING id, name, description, type, created_by, is_archived, created_at, updated_at;
                """,
                clean_name, description, type, actor_id
            )
            channel_id = row["id"]

            # 2. Add creator as owner member
            await conn.execute(
                """
                INSERT INTO rw_channel_members (channel_id, user_id, role)
                VALUES ($1, $2, 'owner')
                ON CONFLICT (channel_id, user_id) DO NOTHING;
                """,
                channel_id, actor_id
            )

            # 3. Add other members if specified
            if member_ids:
                for mid in member_ids:
                    if mid != actor_id:
                        await conn.execute(
                            """
                            INSERT INTO rw_channel_members (channel_id, user_id, role)
                            VALUES ($1, $2, 'member')
                            ON CONFLICT (channel_id, user_id) DO NOTHING;
                            """,
                            channel_id, mid
                        )
            elif type == "public":
                # For public channels, add all active organization users
                await conn.execute(
                    """
                    INSERT INTO rw_channel_members (channel_id, user_id, role)
                    SELECT $1, id, 'member'
                    FROM rw_users
                    WHERE is_active = TRUE AND id != $2
                    ON CONFLICT (channel_id, user_id) DO NOTHING;
                    """,
                    channel_id, actor_id
                )

            return Channel(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                type=row["type"],
                created_by=row["created_by"],
                is_archived=row["is_archived"],
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )
