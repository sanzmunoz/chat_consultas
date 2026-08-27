from typing import Optional, List, Tuple
from uuid import UUID
from datetime import datetime
from src.domain.entities.user import User
from src.domain.ports.user_repository import UserRepositoryPort

class ListUsersUseCase:
    def __init__(self, user_repo: UserRepositoryPort):
        self.user_repo = user_repo

    async def execute(
        self,
        search: Optional[str] = None,
        role: Optional[str] = None,
        cursor_created_at: Optional[datetime] = None,
        cursor_id: Optional[UUID] = None,
        limit: int = 20
    ) -> List[Tuple[User, int, int]]:
        """
        Invokes stored procedure rw_sp_query_users returning users with metrics.
        """
        return await self.user_repo.query_users(
            search=search,
            role=role,
            cursor_created_at=cursor_created_at,
            cursor_id=cursor_id,
            limit=limit
        )
