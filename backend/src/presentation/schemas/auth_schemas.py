from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID

class LoginRequest(BaseModel):
    username_or_email: str = Field(..., min_length=3, description="Username or email address")
    password: str = Field(..., min_length=4, description="User password")

class UserSummary(BaseModel):
    id: UUID
    username: str
    email: str
    display_name: str
    role: str
    position: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900
    user: Optional[UserSummary] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=10, description="Rotatable refresh token")

class UserProfileResponse(BaseModel):
    id: UUID
    username: str
    email: str
    display_name: str
    role: str
    position: str
