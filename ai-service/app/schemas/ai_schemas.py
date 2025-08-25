from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class Message(BaseModel):
    """Represents a single message in a conversation"""
    role: str = Field(..., description="Role of the message sender (user, assistant, system)")
    content: str = Field(..., description="Content of the message")


class GenerateRequest(BaseModel):
    """Request for AI text generation"""
    model: Optional[str] = Field(default=None, description="Model ID to use for generation")
    messages: List[Message] = Field(..., description="List of messages in the conversation")
    parameters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Generation parameters (temperature, max_tokens, etc.)"
    )


class GenerateResponse(BaseModel):
    """Response from AI text generation"""
    response: str = Field(..., description="Generated response text")
    model: str = Field(..., description="Model ID used for generation")
    usage: Dict[str, int] = Field(..., description="Token usage statistics")
