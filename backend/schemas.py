from datetime import datetime

from pydantic import EmailStr
from pydantic import BaseModel, Field


class UserRead(BaseModel):
    id: str
    username: str
    email: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class ConversationCreate(BaseModel):
    title: str | None = Field(default=None, max_length=255)


class ConversationRead(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime


class MessageRead(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    created_at: datetime


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)
    conversation_id: str = Field(..., min_length=1)


class AskResponse(BaseModel):
    answer: str
    sources: list[str]
    matched: bool
    standalone_question: str
    conversation_id: str
