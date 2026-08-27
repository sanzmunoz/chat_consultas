from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000, description="Message text content")
    status: str = Field(default="sent", pattern="^(pending|sent|failed)$")
    msg_ref: Optional[str] = None

class EditMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000, description="Updated message content")

class MessageResponse(BaseModel):
    id: UUID
    msg_ref: Optional[str] = None
    channel_id: UUID
    author_id: UUID
    author_name: Optional[str] = None
    author_username: Optional[str] = None
    author_position: Optional[str] = None
    content: str
    original_content: Optional[str] = None
    status: str
    is_edited: bool
    edited_at: Optional[datetime] = None
    is_deleted: bool
    created_at: datetime
    read_count: int = 0
    is_read_by_me: bool = False

class KeysetMessageListResponse(BaseModel):
    messages: List[MessageResponse]
    next_cursor_created_at: Optional[datetime] = None
    next_cursor_id: Optional[UUID] = None
    has_more: bool = False

class SearchMessageItemResponse(BaseModel):
    id: UUID
    msg_ref: Optional[str] = None
    channel_id: UUID
    channel_name: str
    author_id: UUID
    author_name: str
    author_username: str
    content: str
    highlighted_content: Optional[str] = None
    search_rank: float
    created_at: datetime
