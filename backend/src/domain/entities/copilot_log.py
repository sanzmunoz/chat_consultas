from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from uuid import UUID

@dataclass
class CopilotCitation:
    msg_ref: str
    channel_name: str
    author_name: str
    content_snippet: str
    similarity_score: float

@dataclass
class CopilotQueryResponse:
    query: str
    response: str
    citations: List[CopilotCitation]
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model: str
    prompt_version: str

@dataclass
class CopilotTokenUsage:
    user_id: UUID
    display_name: str
    email: str
    total_queries: int
    total_prompt_tokens: int
    total_completion_tokens: int
    total_tokens_used: int
    last_query_at: Optional[datetime] = None
