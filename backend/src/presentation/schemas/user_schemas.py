from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class UserItemResponse(BaseModel):
    id: UUID
    username: str
    email: str
    display_name: str
    role: str
    position: str
    is_active: bool
    created_at: datetime
    channels_count: int
    messages_count: int

class UserListResponse(BaseModel):
    users: List[UserItemResponse]
    next_cursor_created_at: Optional[datetime] = None
    next_cursor_id: Optional[UUID] = None

class EditUserRequest(BaseModel):
    display_name: Optional[str] = Field(None, min_length=2, max_length=100)
    position: Optional[str] = Field(None, min_length=2, max_length=80)
    role: Optional[str] = Field(None, pattern="^(admin|member)$")
