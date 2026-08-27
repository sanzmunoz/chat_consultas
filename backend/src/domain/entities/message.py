from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from uuid import UUID

@dataclass
class Message:
    id: UUID
    msg_ref: Optional[str]
    channel_id: UUID
    author_id: UUID
    content: str
    original_content: Optional[str] = None
    embedding: Optional[List[float]] = None
    is_edited: bool = False
    edited_at: Optional[datetime] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    status: str = "sent"  # 'pending' | 'sent' | 'failed'
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # Joined view properties
    author_name: Optional[str] = None
    author_username: Optional[str] = None
    author_position: Optional[str] = None
    read_count: int = 0
    is_read_by_me: bool = False
    highlighted_content: Optional[str] = None
    search_rank: Optional[float] = None
