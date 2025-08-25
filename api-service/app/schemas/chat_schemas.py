from pydantic import BaseModel, Field, UUID4
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .settings_schemas import ChatSettings


class ChatSessionBase(BaseModel):
    """Base schema for chat sessions"""
    title: str = Field(..., min_length=1, max_length=500)
    model_name: str = Field(default="facebook/blenderbot-400M-distill", max_length=100)
    is_archived: bool = Field(default=False)
    is_pinned: bool = Field(default=False)


class ChatSessionCreate(ChatSessionBase):
    """Schema for creating a chat session"""
    session_id: str = Field(..., min_length=1)


class ChatSessionUpdate(BaseModel):
    """Schema for updating a chat session"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    model_name: Optional[str] = Field(None, max_length=100)
    is_archived: Optional[bool] = None
    is_pinned: Optional[bool] = None


# ChatSettings schemas moved to settings_schemas.py to avoid duplication


class MessageBase(BaseModel):
    """Base schema for messages"""
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., min_length=1)
    message_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class MessageResponse(MessageBase):
    """Schema for message response"""
    id: UUID4
    session_id: UUID4
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatSession(ChatSessionBase):
    """Schema for chat session response"""
    id: UUID4
    session_id: str
    message_count: int = 0
    created_at: datetime
    updated_at: datetime
    last_message_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ChatSessionWithMessages(ChatSession):
    """Schema for chat session with messages"""
    messages: List[MessageResponse] = []
    settings: Optional[Dict[str, Any]] = None  # Use Dict instead of forward ref


class ChatSessionWithStats(ChatSession):
    """Schema for chat session with statistics"""
    message_count: int = 0
    last_message_preview: Optional[str] = None


class ChatListResponse(BaseModel):
    """Schema for chat list response"""
    chats: List[ChatSessionWithStats]
    total: int
    page: int
    per_page: int
    has_more: bool


class CreateChatRequest(BaseModel):
    """Schema for creating a new chat request"""
    title: Optional[str] = None
    model_name: str = Field(default="facebook/blenderbot-400M-distill")
    initial_message: Optional[str] = None


class CreateChatResponse(BaseModel):
    """Schema for create chat response"""
    chat: ChatSession
    message: Optional[MessageResponse] = None
