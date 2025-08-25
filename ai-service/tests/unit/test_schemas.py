"""
Unit tests for Pydantic schema validation.

This module tests all Pydantic models to ensure proper validation,
serialization, and error handling for API requests and responses.
"""

import pytest
from typing import List, Dict, Any
from pydantic import ValidationError

from app.schemas.ai_schemas import (
    Message, GenerateRequest, GenerateResponse
)


class TestMessage:
    """Test Message schema validation."""
    
    def test_valid_message_creation(self):
        """Test creating valid messages with all roles."""
        # Test user message
        user_msg = Message(role="user", content="Hello, how are you?")
        assert user_msg.role == "user"
        assert user_msg.content == "Hello, how are you?"
        
        # Test assistant message
        assistant_msg = Message(role="assistant", content="I'm doing well!")
        assert assistant_msg.role == "assistant"
        assert assistant_msg.content == "I'm doing well!"
        
        # Test system message
        system_msg = Message(role="system", content="You are a helpful assistant.")
        assert system_msg.role == "system"
        assert system_msg.content == "You are a helpful assistant."
    
    def test_message_with_empty_content(self):
        """Test message with empty content."""
        # Empty content should be allowed
        msg = Message(role="user", content="")
        assert msg.content == ""
    
    def test_message_with_whitespace_content(self):
        """Test message with whitespace-only content."""
        msg = Message(role="user", content="   ")
        assert msg.content == "   "
    
    def test_message_missing_required_fields(self):
        """Test message creation with missing required fields."""
        with pytest.raises(ValidationError) as exc_info:
            Message(role="user")  # Missing content
        assert "content" in str(exc_info.value)
        
        with pytest.raises(ValidationError) as exc_info:
            Message(content="Hello")  # Missing role
        assert "role" in str(exc_info.value)
    
    def test_message_serialization(self):
        """Test message serialization to dict."""
        msg = Message(role="user", content="Test message")
        msg_dict = msg.model_dump()
        
        assert msg_dict == {
            "role": "user",
            "content": "Test message"
        }
    
    def test_message_from_dict(self):
        """Test creating message from dictionary."""
        msg_data = {"role": "assistant", "content": "Response"}
        msg = Message(**msg_data)
        
        assert msg.role == "assistant"
        assert msg.content == "Response"


class TestGenerateRequest:
    """Test GenerateRequest schema validation."""
    
    def test_valid_generate_request_with_model(self):
        """Test creating valid generate request with model specified."""
        messages = [
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi there!")
        ]
        
        request = GenerateRequest(
            model="gpt2",
            messages=messages,
            parameters={"temperature": 0.7, "max_tokens": 100}
        )
        
        assert request.model == "gpt2"
        assert len(request.messages) == 2
        assert request.parameters["temperature"] == 0.7
        assert request.parameters["max_tokens"] == 100
    
    def test_generate_request_without_model(self):
        """Test generate request without model (should be None)."""
        messages = [Message(role="user", content="Hello")]
        request = GenerateRequest(messages=messages)
        
        assert request.model is None
        assert request.parameters is None
    
    def test_generate_request_without_parameters(self):
        """Test generate request without parameters (should be None)."""
        messages = [Message(role="user", content="Hello")]
        request = GenerateRequest(model="test-model", messages=messages)
        
        assert request.parameters is None
    
    def test_generate_request_empty_parameters(self):
        """Test generate request with empty parameters dict."""
        messages = [Message(role="user", content="Hello")]
        request = GenerateRequest(
            model="test-model", 
            messages=messages,
            parameters={}
        )
        
        assert request.parameters == {}
    
    def test_generate_request_missing_messages(self):
        """Test generate request with missing messages field."""
        with pytest.raises(ValidationError) as exc_info:
            GenerateRequest(model="test")  # Missing messages
        assert "messages" in str(exc_info.value)
    
    def test_generate_request_empty_messages(self):
        """Test generate request with empty messages list."""
        request = GenerateRequest(model="test-model", messages=[])
        assert request.messages == []
    
    def test_generate_request_various_parameters(self):
        """Test generate request with various parameter types."""
        messages = [Message(role="user", content="Test")]
        
        # Test with different parameter types
        parameters = {
            "temperature": 0.8,
            "max_tokens": 150,
            "top_p": 0.9,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "stop": ["\\n", "Human:", "Assistant:"],
            "stream": False
        }
        
        request = GenerateRequest(
            model="test-model",
            messages=messages,
            parameters=parameters
        )
        
        assert request.parameters == parameters


class TestGenerateResponse:
    """Test GenerateResponse schema validation."""
    
    def test_valid_generate_response(self):
        """Test creating valid generate response."""
        usage = {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
        
        response = GenerateResponse(
            response="This is a test response.",
            model="test-model",
            usage=usage
        )
        
        assert response.response == "This is a test response."
        assert response.model == "test-model"
        assert response.usage == usage
    
    def test_generate_response_empty_response(self):
        """Test generate response with empty response text."""
        usage = {"prompt_tokens": 5, "completion_tokens": 0, "total_tokens": 5}
        
        response = GenerateResponse(
            response="",
            model="test-model",
            usage=usage
        )
        
        assert response.response == ""
    
    def test_generate_response_missing_required_fields(self):
        """Test generate response with missing required fields."""
        with pytest.raises(ValidationError):
            GenerateResponse(model="test", usage={})  # Missing response
        
        with pytest.raises(ValidationError):
            GenerateResponse(response="test", usage={})  # Missing model
        
        with pytest.raises(ValidationError):
            GenerateResponse(response="test", model="test")  # Missing usage


class TestSchemaInteraction:
    """Test interaction between different schemas."""
    
    def test_generate_request_with_multiple_message_types(self):
        """Test generate request with system, user, and assistant messages."""
        messages = [
            Message(role="system", content="You are a helpful assistant."),
            Message(role="user", content="Hello!"),
            Message(role="assistant", content="Hi there!"),
            Message(role="user", content="How are you?")
        ]
        
        request = GenerateRequest(
            model="test-model",
            messages=messages,
            parameters={"temperature": 0.8}
        )
        
        assert len(request.messages) == 4
        assert request.messages[0].role == "system"
        assert request.messages[1].role == "user"
        assert request.messages[2].role == "assistant"
        assert request.messages[3].role == "user"
    
    def test_generate_request_with_conversation_history(self):
        """Test generate request with complete conversation history."""
        messages = []
        
        # Add multiple conversation turns
        for i in range(3):
            messages.append(Message(role="user", content=f"User message {i}"))
            messages.append(Message(role="assistant", content=f"Assistant response {i}"))
        
        # Add final user message
        messages.append(Message(role="user", content="Final question"))
        
        request = GenerateRequest(
            model="test-model",
            messages=messages,
            parameters={"temperature": 0.7, "max_tokens": 200}
        )
        
        assert len(request.messages) == 7  # 3*2 + 1
        user_messages = [msg for msg in request.messages if msg.role == "user"]
        assistant_messages = [msg for msg in request.messages if msg.role == "assistant"]
        
        assert len(user_messages) == 4
        assert len(assistant_messages) == 3
