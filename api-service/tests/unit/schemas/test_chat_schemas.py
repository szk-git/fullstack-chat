"""
Unit tests for chat schemas validation.

This module tests all chat-related Pydantic models to ensure proper validation,
serialization, and error handling.
"""

import pytest
from typing import Dict, Any
from uuid import uuid4
from datetime import datetime
from pydantic import ValidationError

from app.schemas.chat_schemas import (
    ChatSessionBase, ChatSessionCreate, ChatSessionUpdate,
    MessageBase, MessageResponse, ChatSession, ChatSessionWithMessages,
    ChatSessionWithStats, ChatListResponse, CreateChatRequest, CreateChatResponse
)


class TestChatSessionBase:
    """Test ChatSessionBase schema validation."""
    
    def test_valid_chat_session_base_creation(self):
        """Test creating valid chat session base."""
        data = {
            "title": "Test Chat Session",
            "model_name": "facebook/blenderbot-400M-distill",
            "is_archived": False,
            "is_pinned": False
        }
        
        session = ChatSessionBase(**data)
        assert session.title == "Test Chat Session"
        assert session.model_name == "facebook/blenderbot-400M-distill"
        assert session.is_archived is False
        assert session.is_pinned is False
    
    def test_valid_chat_session_base_defaults(self):
        """Test chat session base with default values."""
        data = {"title": "Test Chat"}
        
        session = ChatSessionBase(**data)
        assert session.title == "Test Chat"
        assert session.model_name == "facebook/blenderbot-400M-distill"
        assert session.is_archived is False
        assert session.is_pinned is False
    
    def test_title_validation_empty(self):
        """Test title validation with empty string."""
        with pytest.raises(ValidationError) as exc_info:
            ChatSessionBase(title="")
        assert "at least 1 character" in str(exc_info.value)
    
    def test_title_validation_too_long(self):
        """Test title validation with too long string."""
        long_title = "x" * 501
        with pytest.raises(ValidationError) as exc_info:
            ChatSessionBase(title=long_title)
        assert "at most 500 characters" in str(exc_info.value)
    
    def test_model_name_validation_too_long(self):
        """Test model name validation with too long string."""
        long_model = "x" * 101
        with pytest.raises(ValidationError) as exc_info:
            ChatSessionBase(title="Test", model_name=long_model)
        assert "at most 100 characters" in str(exc_info.value)
    
    def test_boolean_fields_validation(self):
        """Test boolean field validation."""
        # Valid boolean values
        session = ChatSessionBase(
            title="Test",
            is_archived=True,
            is_pinned=True
        )
        assert session.is_archived is True
        assert session.is_pinned is True
        
        # Test string boolean conversion
        session = ChatSessionBase(
            title="Test",
            is_archived="true",
            is_pinned="false"
        )
        assert session.is_archived is True
        assert session.is_pinned is False


class TestChatSessionCreate:
    """Test ChatSessionCreate schema validation."""
    
    def test_valid_chat_session_create(self):
        """Test creating valid chat session creation request."""
        data = {
            "title": "New Chat",
            "session_id": "test-session-123",
            "model_name": "gpt2"
        }
        
        session = ChatSessionCreate(**data)
        assert session.title == "New Chat"
        assert session.session_id == "test-session-123"
        assert session.model_name == "gpt2"
    
    def test_session_id_validation_empty(self):
        """Test session_id validation with empty string."""
        with pytest.raises(ValidationError) as exc_info:
            ChatSessionCreate(title="Test", session_id="")
        assert "at least 1 character" in str(exc_info.value)
    
    def test_session_id_required(self):
        """Test session_id is required."""
        with pytest.raises(ValidationError) as exc_info:
            ChatSessionCreate(title="Test")
        assert "session_id" in str(exc_info.value)
    
    def test_inherits_base_validation(self):
        """Test that ChatSessionCreate inherits base validation."""
        with pytest.raises(ValidationError) as exc_info:
            ChatSessionCreate(title="", session_id="test")
        assert "at least 1 character" in str(exc_info.value)


class TestChatSessionUpdate:
    """Test ChatSessionUpdate schema validation."""
    
    def test_valid_partial_update(self):
        """Test valid partial update with some fields."""
        data = {
            "title": "Updated Title",
            "is_archived": True
        }
        
        update = ChatSessionUpdate(**data)
        assert update.title == "Updated Title"
        assert update.is_archived is True
        assert update.model_name is None
        assert update.is_pinned is None
    
    def test_empty_update(self):
        """Test update with no fields provided."""
        update = ChatSessionUpdate()
        assert update.title is None
        assert update.model_name is None
        assert update.is_archived is None
        assert update.is_pinned is None
    
    def test_all_fields_update(self):
        """Test update with all fields provided."""
        data = {
            "title": "Full Update",
            "model_name": "new-model",
            "is_archived": True,
            "is_pinned": False
        }
        
        update = ChatSessionUpdate(**data)
        assert update.title == "Full Update"
        assert update.model_name == "new-model"
        assert update.is_archived is True
        assert update.is_pinned is False
    
    def test_validation_on_provided_fields(self):
        """Test validation applies to provided fields."""
        with pytest.raises(ValidationError) as exc_info:
            ChatSessionUpdate(title="")
        assert "at least 1 character" in str(exc_info.value)


class TestMessageBase:
    """Test MessageBase schema validation."""
    
    def test_valid_user_message(self):
        """Test valid user message creation."""
        data = {
            "role": "user",
            "content": "Hello, how are you?",
            "message_metadata": {"source": "web"}
        }
        
        message = MessageBase(**data)
        assert message.role == "user"
        assert message.content == "Hello, how are you?"
        assert message.message_metadata == {"source": "web"}
    
    def test_valid_assistant_message(self):
        """Test valid assistant message creation."""
        data = {
            "role": "assistant",
            "content": "I'm doing well, thank you!"
        }
        
        message = MessageBase(**data)
        assert message.role == "assistant"
        assert message.content == "I'm doing well, thank you!"
        assert message.message_metadata == {}  # Default empty dict
    
    def test_valid_system_message(self):
        """Test valid system message creation."""
        data = {
            "role": "system",
            "content": "You are a helpful assistant."
        }
        
        message = MessageBase(**data)
        assert message.role == "system"
        assert message.content == "You are a helpful assistant."
    
    def test_role_validation_invalid(self):
        """Test role validation with invalid role."""
        invalid_roles = ["invalid", "admin", "moderator", ""]
        
        for role in invalid_roles:
            with pytest.raises(ValidationError) as exc_info:
                MessageBase(role=role, content="Test content")
            assert "String should match pattern" in str(exc_info.value)
    
    def test_content_validation_empty(self):
        """Test content validation with empty string."""
        with pytest.raises(ValidationError) as exc_info:
            MessageBase(role="user", content="")
        assert "at least 1 character" in str(exc_info.value)
    
    def test_content_validation_required(self):
        """Test content is required."""
        with pytest.raises(ValidationError) as exc_info:
            MessageBase(role="user")
        assert "content" in str(exc_info.value)
    
    def test_metadata_default_factory(self):
        """Test message metadata default factory."""
        message1 = MessageBase(role="user", content="Test 1")
        message2 = MessageBase(role="user", content="Test 2")
        
        # Each instance should have its own dict
        message1.message_metadata["key"] = "value1"
        assert message2.message_metadata == {}
        assert message1.message_metadata == {"key": "value1"}


class TestMessageResponse:
    """Test MessageResponse schema validation."""
    
    def test_valid_message_response(self):
        """Test valid message response creation."""
        message_id = uuid4()
        session_id = uuid4()
        created_at = datetime.utcnow()
        
        data = {
            "id": message_id,
            "session_id": session_id,
            "role": "user",
            "content": "Test message",
            "message_metadata": {"test": "data"},
            "created_at": created_at
        }
        
        message = MessageResponse(**data)
        assert message.id == message_id
        assert message.session_id == session_id
        assert message.role == "user"
        assert message.content == "Test message"
        assert message.created_at == created_at
    
    def test_inherits_base_validation(self):
        """Test MessageResponse inherits MessageBase validation."""
        with pytest.raises(ValidationError):
            MessageResponse(
                id=uuid4(),
                session_id=uuid4(),
                role="invalid_role",
                content="Test",
                created_at=datetime.utcnow()
            )


class TestChatSession:
    """Test ChatSession schema validation."""
    
    def test_valid_chat_session(self):
        """Test valid chat session creation."""
        session_id_uuid = uuid4()
        created_at = datetime.utcnow()
        updated_at = datetime.utcnow()
        
        data = {
            "id": session_id_uuid,
            "session_id": "test-session-123",
            "title": "Test Chat",
            "model_name": "test-model",
            "is_archived": False,
            "is_pinned": True,
            "message_count": 5,
            "created_at": created_at,
            "updated_at": updated_at,
            "last_message_at": created_at
        }
        
        session = ChatSession(**data)
        assert session.id == session_id_uuid
        assert session.session_id == "test-session-123"
        assert session.message_count == 5
        assert session.last_message_at == created_at
    
    def test_optional_last_message_at(self):
        """Test last_message_at can be None."""
        data = {
            "id": uuid4(),
            "session_id": "test-session",
            "title": "Test",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_message_at": None
        }
        
        session = ChatSession(**data)
        assert session.last_message_at is None
    
    def test_message_count_default(self):
        """Test message_count default value."""
        data = {
            "id": uuid4(),
            "session_id": "test-session",
            "title": "Test",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        session = ChatSession(**data)
        assert session.message_count == 0


class TestChatSessionWithMessages:
    """Test ChatSessionWithMessages schema validation."""
    
    def test_valid_session_with_messages(self):
        """Test valid chat session with messages."""
        session_uuid = uuid4()
        message_uuid = uuid4()
        now = datetime.utcnow()
        
        data = {
            "id": session_uuid,
            "session_id": "test-session",
            "title": "Test Chat",
            "created_at": now,
            "updated_at": now,
            "messages": [
                {
                    "id": message_uuid,
                    "session_id": session_uuid,
                    "role": "user",
                    "content": "Hello",
                    "created_at": now,
                    "message_metadata": {}
                }
            ],
            "settings": {"temperature": "0.7"}
        }
        
        session = ChatSessionWithMessages(**data)
        assert len(session.messages) == 1
        assert session.messages[0].content == "Hello"
        assert session.settings == {"temperature": "0.7"}
    
    def test_empty_messages_and_settings(self):
        """Test session with empty messages and no settings."""
        data = {
            "id": uuid4(),
            "session_id": "test-session",
            "title": "Test Chat",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "messages": [],
            "settings": None
        }
        
        session = ChatSessionWithMessages(**data)
        assert session.messages == []
        assert session.settings is None


class TestChatListResponse:
    """Test ChatListResponse schema validation."""
    
    def test_valid_chat_list_response(self):
        """Test valid chat list response."""
        session_data = {
            "id": uuid4(),
            "session_id": "test-session",
            "title": "Test Chat",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "message_count": 5,
            "last_message_preview": "Hello there"
        }
        
        data = {
            "chats": [ChatSessionWithStats(**session_data)],
            "total": 1,
            "page": 1,
            "per_page": 10,
            "has_more": False
        }
        
        response = ChatListResponse(**data)
        assert len(response.chats) == 1
        assert response.total == 1
        assert response.has_more is False
    
    def test_empty_chat_list(self):
        """Test empty chat list response."""
        data = {
            "chats": [],
            "total": 0,
            "page": 1,
            "per_page": 10,
            "has_more": False
        }
        
        response = ChatListResponse(**data)
        assert response.chats == []
        assert response.total == 0


class TestCreateChatRequest:
    """Test CreateChatRequest schema validation."""
    
    def test_valid_create_chat_request(self):
        """Test valid create chat request."""
        data = {
            "title": "New Chat",
            "model_name": "custom-model",
            "initial_message": "Hello, let's start chatting!"
        }
        
        request = CreateChatRequest(**data)
        assert request.title == "New Chat"
        assert request.model_name == "custom-model"
        assert request.initial_message == "Hello, let's start chatting!"
    
    def test_minimal_create_chat_request(self):
        """Test minimal create chat request with defaults."""
        request = CreateChatRequest()
        assert request.title is None
        assert request.model_name == "facebook/blenderbot-400M-distill"
        assert request.initial_message is None
    
    def test_partial_create_chat_request(self):
        """Test partial create chat request."""
        data = {"title": "Custom Title"}
        
        request = CreateChatRequest(**data)
        assert request.title == "Custom Title"
        assert request.model_name == "facebook/blenderbot-400M-distill"
        assert request.initial_message is None


class TestCreateChatResponse:
    """Test CreateChatResponse schema validation."""
    
    def test_valid_create_chat_response_with_message(self):
        """Test valid create chat response with initial message."""
        session_uuid = uuid4()
        message_uuid = uuid4()
        now = datetime.utcnow()
        
        chat_data = {
            "id": session_uuid,
            "session_id": "test-session",
            "title": "New Chat",
            "created_at": now,
            "updated_at": now
        }
        
        message_data = {
            "id": message_uuid,
            "session_id": session_uuid,
            "role": "user",
            "content": "Initial message",
            "created_at": now,
            "message_metadata": {}
        }
        
        data = {
            "chat": ChatSession(**chat_data),
            "message": MessageResponse(**message_data)
        }
        
        response = CreateChatResponse(**data)
        assert response.chat.title == "New Chat"
        assert response.message.content == "Initial message"
    
    def test_valid_create_chat_response_without_message(self):
        """Test valid create chat response without initial message."""
        chat_data = {
            "id": uuid4(),
            "session_id": "test-session",
            "title": "New Chat",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        data = {
            "chat": ChatSession(**chat_data),
            "message": None
        }
        
        response = CreateChatResponse(**data)
        assert response.chat.title == "New Chat"
        assert response.message is None


class TestSchemaInteractions:
    """Test interactions between different schemas."""
    
    def test_complex_chat_session_with_all_data(self):
        """Test complex chat session with messages and settings."""
        session_uuid = uuid4()
        now = datetime.utcnow()
        
        # Create multiple messages
        messages = []
        for i, role in enumerate(["user", "assistant", "user"]):
            message_data = {
                "id": uuid4(),
                "session_id": session_uuid,
                "role": role,
                "content": f"Message {i+1}",
                "created_at": now,
                "message_metadata": {"order": i+1}
            }
            messages.append(MessageResponse(**message_data))
        
        session_data = {
            "id": session_uuid,
            "session_id": "complex-session",
            "title": "Complex Chat Session",
            "model_name": "advanced-model",
            "is_archived": False,
            "is_pinned": True,
            "message_count": 3,
            "created_at": now,
            "updated_at": now,
            "last_message_at": now,
            "messages": messages,
            "settings": {
                "temperature": "0.8",
                "max_tokens": 2000,
                "system_prompt": "Be helpful and concise"
            }
        }
        
        session = ChatSessionWithMessages(**session_data)
        assert len(session.messages) == 3
        assert session.messages[0].role == "user"
        assert session.messages[1].role == "assistant"
        assert session.settings["temperature"] == "0.8"
    
    def test_schema_serialization_compatibility(self):
        """Test that schemas can be properly serialized."""
        session_data = {
            "id": uuid4(),
            "session_id": "serialize-test",
            "title": "Serialization Test",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        session = ChatSession(**session_data)
        
        # Test model_dump works
        serialized = session.model_dump()
        assert serialized["title"] == "Serialization Test"
        assert "id" in serialized
        assert "created_at" in serialized
    
    def test_uuid_field_validation(self):
        """Test UUID field validation in schemas."""
        # Valid UUID4 string should work
        valid_uuid4_1 = uuid4()
        valid_uuid4_2 = uuid4()
        
        session = MessageResponse(
            id=valid_uuid4_1,
            session_id=valid_uuid4_2,
            role="user",
            content="Test",
            created_at=datetime.utcnow()
        )
        assert session.id == valid_uuid4_1
        
        # Invalid UUID should fail
        with pytest.raises(ValidationError):
            MessageResponse(
                id="not-a-uuid",
                session_id=uuid4(),
                role="user",
                content="Test",
                created_at=datetime.utcnow()
            )
