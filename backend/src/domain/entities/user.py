from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

@dataclass
class User:
    id: UUID
    username: str
    email: str
    password_hash: str
    display_name: str
    role: str  # 'admin' | 'member'
    position: str
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"
