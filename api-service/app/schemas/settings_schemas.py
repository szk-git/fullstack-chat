from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime


class ChatSettingsBase(BaseModel):
    """Base chat settings schema"""
    temperature: Optional[str] = Field(default="0.7", description="Temperature for AI model")
    max_tokens: Optional[int] = Field(default=1000, ge=1, le=50000, description="Maximum tokens for response")
    system_prompt: Optional[str] = Field(default=None, description="System prompt for AI model")


class ChatSettingsCreate(ChatSettingsBase):
    """Schema for creating chat settings"""
    session_id: UUID


class ChatSettingsUpdate(ChatSettingsBase):
    """Schema for updating chat settings"""
    pass


class ChatSettings(ChatSettingsBase):
    """Schema for returning chat settings"""
    session_id: str  # Changed from UUID to str for API response
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @classmethod
    def from_orm(cls, obj):
        # Convert from database model, excluding model_parameters field
        data = {
            'session_id': str(obj.session_id),  # Convert UUID to string
            'temperature': obj.temperature,
            'max_tokens': obj.max_tokens,
            'system_prompt': obj.system_prompt,
            'created_at': obj.created_at,
            'updated_at': obj.updated_at
        }
        return cls(**data)


class ChatSettingsResponse(BaseModel):
    """Response schema for chat settings operations"""
    settings: ChatSettings
    message: str = "Settings updated successfully"
