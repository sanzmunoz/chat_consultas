from typing import Optional, List, Tuple
from uuid import UUID
from datetime import datetime
from src.domain.entities.user import User
from src.domain.ports.user_repository import UserRepositoryPort
from src.infrastructure.database.pool import get_connection_with_actor, get_pool

class PgUserRepository(UserRepositoryPort):

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        pool = get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, username, email, password_hash, display_name, role, position, is_active, created_at, updated_at
                FROM rw_users
                WHERE id = $1;
                """,
                user_id
            )
            if not row:
                return None
            return User(
                id=row["id"],
                username=row["username"],
                email=row["email"],
                password_hash=row["password_hash"],
                display_name=row["display_name"],
                role=row["role"],
                position=row["position"],
                is_active=row["is_active"],
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )

    async def get_by_email(self, email: str) -> Optional[User]:
        pool = get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, username, email, password_hash, display_name, role, position, is_active, created_at, updated_at
                FROM rw_users
                WHERE email = $1;
                """,
                email.strip().lower()
            )
            if not row:
                return None
            return User(
                id=row["id"],
                username=row["username"],
                email=row["email"],
                password_hash=row["password_hash"],
                display_name=row["display_name"],
                role=row["role"],
                position=row["position"],
                is_active=row["is_active"],
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )

    async def get_by_username(self, username: str) -> Optional[User]:
        pool = get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, username, email, password_hash, display_name, role, position, is_active, created_at, updated_at
                FROM rw_users
                WHERE username = $1;
                """,
                username.strip().lower()
            )
            if not row:
                return None
            return User(
                id=row["id"],
                username=row["username"],
                email=row["email"],
                password_hash=row["password_hash"],
                display_name=row["display_name"],
                role=row["role"],
                position=row["position"],
                is_active=row["is_active"],
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )

    async def query_users(
        self,
        search: Optional[str] = None,
        role: Optional[str] = None,
        cursor_created_at: Optional[datetime] = None,
        cursor_id: Optional[UUID] = None,
        limit: int = 20
    ) -> List[Tuple[User, int, int]]:
        pool = get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, username, email, display_name, role, "position", is_active, created_at, channels_count, messages_count
                FROM rw_fn_query_users($1, $2, $3, $4, $5);
                """,
                search, role, cursor_created_at, cursor_id, limit
            )
            results = []
            for r in rows:
                user = User(
                    id=r["id"],
                    username=r["username"],
                    email=r["email"],
                    password_hash="",  # do not expose password hash
                    display_name=r["display_name"],
                    role=r["role"],
                    position=r["position"],
                    is_active=r["is_active"],
                    created_at=r["created_at"]
                )
                results.append((user, r["channels_count"], r["messages_count"]))
            return results

    async def edit_or_delete_user(
        self,
        target_user_id: UUID,
        action: str,
        display_name: Optional[str] = None,
        position: Optional[str] = None,
        role: Optional[str] = None
    ) -> Tuple[bool, str]:
        # Uses actor propagation from current session
        pool = get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                CALL rw_sp_edit_or_delete_user($1, $2, $3, $4, $5, NULL, NULL);
                """,
                target_user_id, action.upper(), display_name, position, role
            )
            success = row["p_success"] if row and "p_success" in row else True
            message = row["p_message"] if row and "p_message" in row else "Operation completed"
            return success, message

    async def save_refresh_token(self, user_id: UUID, token_hash: str, expires_at: datetime) -> None:
        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO rw_refresh_tokens (user_id, token_hash, expires_at, is_revoked)
                VALUES ($1, $2, $3, FALSE);
                """,
                user_id, token_hash, expires_at
            )

    async def verify_and_rotate_refresh_token(
        self,
        token_hash: str,
        new_token_hash: str,
        new_expires_at: datetime
    ) -> Optional[UUID]:
        pool = get_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                # 1. Fetch valid refresh token
                row = await conn.fetchrow(
                    """
                    SELECT id, user_id, expires_at, is_revoked
                    FROM rw_refresh_tokens
                    WHERE token_hash = $1
                    FOR UPDATE;
                    """,
                    token_hash
                )
                if not row or row["is_revoked"] or row["expires_at"] < datetime.now(row["expires_at"].tzinfo):
                    return None

                user_id = row["user_id"]

                # 2. Revoke old token
                await conn.execute(
                    """
                    UPDATE rw_refresh_tokens
                    SET is_revoked = TRUE
                    WHERE id = $1;
                    """,
                    row["id"]
                )

                # 3. Save new rotated token
                await conn.execute(
                    """
                    INSERT INTO rw_refresh_tokens (user_id, token_hash, expires_at, is_revoked)
                    VALUES ($1, $2, $3, FALSE);
                    """,
                    user_id, new_token_hash, new_expires_at
                )

                return user_id
