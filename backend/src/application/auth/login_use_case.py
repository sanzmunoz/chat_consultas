from typing import Tuple, Optional, Dict, Any
from src.domain.ports.user_repository import UserRepositoryPort
from src.infrastructure.auth.hasher import verify_password
from src.infrastructure.auth.jwt_service import create_access_token, generate_refresh_token

class LoginUseCase:
    def __init__(self, user_repo: UserRepositoryPort):
        self.user_repo = user_repo

    async def execute(self, identifier: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticates user via email or username, verifies bcrypt hash,
        generates short-lived access JWT and rotatable refresh token.
        """
        identifier_clean = identifier.strip().lower()
        user = None
        if "@" in identifier_clean:
            user = await self.user_repo.get_by_email(identifier_clean)
        else:
            user = await self.user_repo.get_by_username(identifier_clean)

        if not user or not user.is_active:
            return None

        if not verify_password(password, user.password_hash):
            return None

        # Generate tokens
        access_token = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role,
            display_name=user.display_name,
            position=user.position
        )

        raw_refresh, refresh_hash, expires_at = generate_refresh_token()
        await self.user_repo.save_refresh_token(user.id, refresh_hash, expires_at)

        return {
            "access_token": access_token,
            "refresh_token": raw_refresh,
            "token_type": "bearer",
            "expires_in": 900,  # 15 minutes in seconds
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "display_name": user.display_name,
                "role": user.role,
                "position": user.position
            }
        }
