from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None

class ErrorResponse(BaseModel):
    error: ErrorDetail
    path: str
    correlation_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[Any] = None
