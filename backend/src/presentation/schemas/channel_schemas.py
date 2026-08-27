from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class ChannelSummaryResponse(BaseModel):
    channel_id: UUID
    channel_name: str
    channel_description: Optional[str] = None
    channel_type: str
    is_archived: bool
    user_channel_role: str
    member_count: int
    unread_count: int
    last_message_id: Optional[UUID] = None
    last_message_content: Optional[str] = None
    last_message_created_at: Optional[datetime] = None
    last_message_author_name: Optional[str] = None

class ChannelMemberResponse(BaseModel):
    membership_id: UUID
    user_id: UUID
    display_name: str
    username: str
    email: str
    position: str
    role: str
    joined_at: datetime

class CreateChannelRequest(BaseModel):
    name: str
    description: Optional[str] = None
    type: str = "public"
    member_ids: Optional[list[UUID]] = None

class CreateChannelResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    type: str
    created_by: UUID
    is_archived: bool
    created_at: datetime
    updated_at: datetime
