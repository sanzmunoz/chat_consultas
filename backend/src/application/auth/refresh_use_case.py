from typing import Optional, Dict, Any
from src.domain.ports.user_repository import UserRepositoryPort
from src.infrastructure.auth.jwt_service import (
    create_access_token,
    generate_refresh_token,
    hash_refresh_token
)

class RefreshUseCase:
    def __init__(self, user_repo: UserRepositoryPort):
        self.user_repo = user_repo

    async def execute(self, raw_refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Validates the incoming refresh token and implements single-use rotation.
        Revokes old token and issues new access and refresh tokens.
        """
        if not raw_refresh_token:
            return None

        old_token_hash = hash_refresh_token(raw_refresh_token)
        new_raw_refresh, new_refresh_hash, new_expires_at = generate_refresh_token()

        user_id = await self.user_repo.verify_and_rotate_refresh_token(
            old_token_hash, new_refresh_hash, new_expires_at
        )

        if not user_id:
            return None

        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            return None

        access_token = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role,
            display_name=user.display_name,
            position=user.position
        )

        return {
            "access_token": access_token,
            "refresh_token": new_raw_refresh,
            "token_type": "bearer",
            "expires_in": 900
        }
