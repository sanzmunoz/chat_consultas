from typing import Protocol, Optional, List, Tuple
from uuid import UUID
from datetime import datetime
from src.domain.entities.user import User

class UserRepositoryPort(Protocol):
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        ...

    async def get_by_email(self, email: str) -> Optional[User]:
        ...

    async def get_by_username(self, username: str) -> Optional[User]:
        ...

    async def query_users(
        self,
        search: Optional[str] = None,
        role: Optional[str] = None,
        cursor_created_at: Optional[datetime] = None,
        cursor_id: Optional[UUID] = None,
        limit: int = 20
    ) -> List[Tuple[User, int, int]]:  # returns (User, channels_count, messages_count)
        ...

    async def edit_or_delete_user(
        self,
        target_user_id: UUID,
        action: str,  # 'EDIT' | 'DELETE'
        display_name: Optional[str] = None,
        position: Optional[str] = None,
        role: Optional[str] = None
    ) -> Tuple[bool, str]:
        ...

    async def save_refresh_token(self, user_id: UUID, token_hash: str, expires_at: datetime) -> None:
        ...

    async def verify_and_rotate_refresh_token(self, token_hash: str, new_token_hash: str, new_expires_at: datetime) -> Optional[UUID]:
        ...
