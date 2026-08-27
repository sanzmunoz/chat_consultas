from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

@dataclass
class Channel:
    id: UUID
    name: str
    description: Optional[str]
    type: str  # 'public' | 'private'
    created_by: UUID
    is_archived: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class ChannelConversationSummary:
    channel_id: UUID
    channel_name: str
    channel_description: Optional[str]
    channel_type: str
    is_archived: bool
    user_channel_role: str
    member_count: int
    unread_count: int
    last_message_id: Optional[UUID]
    last_message_content: Optional[str]
    last_message_created_at: Optional[datetime]
    last_message_author_name: Optional[str]
