from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class CopilotQueryRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=2000, description="Natural language question for Copilot")

class CopilotCitationSchema(BaseModel):
    msg_ref: str
    channel_name: str
    author_name: str
    content_snippet: str
    similarity_score: float

class CopilotQueryResponseSchema(BaseModel):
    query: str
    response: str
    citations: List[CopilotCitationSchema]
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model: str
    prompt_version: str

class CopilotUsageResponseSchema(BaseModel):
    user_id: UUID
    display_name: str
    email: str
    total_queries: int
    total_prompt_tokens: int
    total_completion_tokens: int
    total_tokens_used: int
    last_query_at: Optional[datetime] = None
