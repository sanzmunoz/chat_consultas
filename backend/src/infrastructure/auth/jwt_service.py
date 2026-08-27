import os
import jwt
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, Tuple
from uuid import UUID

JWT_SECRET = os.getenv("JWT_SECRET", "super_secret_jwt_key_riwi_chat_2026_at_least_32_chars")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

def create_access_token(user_id: UUID, email: str, role: str, display_name: str, position: str) -> str:
    """Creates a short-lived access JWT containing user identity and claims."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "display_name": display_name,
        "position": position,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def generate_refresh_token() -> Tuple[str, str, datetime]:
    """
    Generates a secure random refresh token, its SHA-256 hash for DB storage,
    and its expiration timestamp.
    """
    raw_token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return raw_token, token_hash, expires_at

def hash_refresh_token(raw_token: str) -> str:
    """Hashes raw refresh token to look up in database."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates signature and expiration of access token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except (jwt.PyJWTError, Exception):
        return None
