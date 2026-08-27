from fastapi import Header, HTTPException, status, Depends
from typing import Optional
from uuid import UUID
from src.domain.entities.user import User
from src.infrastructure.auth.jwt_service import decode_access_token
from src.infrastructure.database.pg_user_repository import PgUserRepository

user_repo = PgUserRepository()

async def get_current_user(authorization: Optional[str] = Header(None)) -> User:
    """
    Extracts user identity exclusively from Bearer JWT in Authorization header.
    Never accepts or relies on user identifiers passed in request bodies.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header. Expected Bearer token.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = authorization.split(" ")[1].strip()
    payload = decode_access_token(token)

    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        user_id = UUID(payload["sub"])
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Corrupted token subject identifier."
        )

    user = await user_repo.get_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated or no longer exists."
        )

    return user

async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Enforces admin privilege check."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required for this action."
        )
    return current_user
