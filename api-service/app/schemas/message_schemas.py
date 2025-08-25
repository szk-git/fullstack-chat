from pydantic import BaseModel, Field, UUID4
from typing import Optional, List, Dict, Any
from datetime import datetime


class MessageBase(BaseModel):
    """Base schema for messages"""
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., min_length=1)
    message_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class MessageCreate(MessageBase):
    """Schema for creating a message"""
    session_id: UUID4


class MessageUpdate(BaseModel):
    """Schema for updating a message"""
    content: Optional[str] = Field(None, min_length=1)
    message_metadata: Optional[Dict[str, Any]] = None


class Message(MessageBase):
    """Schema for message response"""
    id: UUID4
    session_id: UUID4
    created_at: datetime
    
    class Config:
        from_attributes = True


class MessageList(BaseModel):
    """Schema for message list response"""
    messages: List[Message]
    total: int
    page: int
    per_page: int
    has_more: bool


class SendMessageRequest(BaseModel):
    """Schema for sending a message request"""
    content: str = Field(..., min_length=1, max_length=4000)
    model_parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SendMessageResponse(BaseModel):
    """Schema for send message response"""
    user_message: Message
    assistant_message: Message
    chat_id: UUID4
    message_count: int


class MessageSearchRequest(BaseModel):
    """Schema for message search request"""
    query: str = Field(..., min_length=1, max_length=200)
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class MessageSearchResponse(BaseModel):
    """Schema for message search response"""
    messages: List[Message]
    total_matches: int
    query: str


class SystemMessageResponse(BaseModel):
    """Schema for system message response"""
    message: str
    system_message: Message
    chat_id: str
