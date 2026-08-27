from typing import Optional, Tuple
from uuid import UUID
from src.domain.ports.user_repository import UserRepositoryPort

class EditDeleteUserUseCase:
    def __init__(self, user_repo: UserRepositoryPort):
        self.user_repo = user_repo

    async def execute(
        self,
        target_user_id: UUID,
        action: str,  # 'EDIT' | 'DELETE'
        display_name: Optional[str] = None,
        position: Optional[str] = None,
        role: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Invokes stored procedure rw_sp_edit_or_delete_user.
        Enforces business rules:
        - EDIT: User can edit own profile, Admin can edit anyone.
        - DELETE: Logical deactivation with refresh session revocation; Admin only.
        """
        action_clean = action.upper()
        if action_clean not in ("EDIT", "DELETE"):
            return False, "Invalid action. Must be EDIT or DELETE."

        return await self.user_repo.edit_or_delete_user(
            target_user_id=target_user_id,
            action=action_clean,
            display_name=display_name,
            position=position,
            role=role
        )
