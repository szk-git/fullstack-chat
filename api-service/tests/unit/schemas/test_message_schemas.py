"""
Unit tests for message schemas validation.

This module tests all message-related Pydantic models to ensure proper validation,
serialization, and error handling.
"""

import pytest
from typing import Dict, Any
from uuid import uuid4
from datetime import datetime
from pydantic import ValidationError

from app.schemas.message_schemas import (
    MessageBase, MessageCreate, MessageUpdate, Message, MessageList,
    SendMessageRequest, SendMessageResponse, MessageSearchRequest,
    MessageSearchResponse, SystemMessageResponse
)


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
    
    def test_role_validation_valid_roles(self):
        """Test role validation with valid roles."""
        valid_roles = ["user", "assistant", "system"]
        
        for role in valid_roles:
            message = MessageBase(role=role, content="Test content")
            assert message.role == role
    
    def test_role_validation_invalid_roles(self):
        """Test role validation with invalid roles."""
        invalid_roles = ["invalid", "admin", "moderator", "", "USER", "ASSISTANT"]
        
        for role in invalid_roles:
            with pytest.raises(ValidationError) as exc_info:
                MessageBase(role=role, content="Test content")
            assert "String should match pattern" in str(exc_info.value)
    
    def test_content_validation_empty(self):
        """Test content validation with empty string."""
        with pytest.raises(ValidationError) as exc_info:
            MessageBase(role="user", content="")
        assert "at least 1 character" in str(exc_info.value)
    
    def test_content_validation_whitespace_only(self):
        """Test content validation with whitespace only."""
        # Whitespace only should pass min_length validation
        message = MessageBase(role="user", content="   ")
        assert message.content == "   "
        assert len(message.content) >= 1
    
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
    
    def test_metadata_complex_data(self):
        """Test message metadata with complex data types."""
        complex_metadata = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": str(uuid4()),
            "preferences": {
                "theme": "dark",
                "language": "en"
            },
            "tags": ["urgent", "follow-up"],
            "confidence": 0.95,
            "is_flagged": False
        }
        
        message = MessageBase(
            role="user",
            content="Complex metadata test",
            message_metadata=complex_metadata
        )
        assert message.message_metadata == complex_metadata


class TestMessageCreate:
    """Test MessageCreate schema validation."""
    
    def test_valid_message_create(self):
        """Test valid message creation request."""
        session_id = uuid4()
        data = {
            "role": "user",
            "content": "Create message test",
            "session_id": session_id,
            "message_metadata": {"source": "test"}
        }
        
        message = MessageCreate(**data)
        assert message.role == "user"
        assert message.content == "Create message test"
        assert message.session_id == session_id
        assert message.message_metadata == {"source": "test"}
    
    def test_session_id_required(self):
        """Test session_id is required."""
        with pytest.raises(ValidationError) as exc_info:
            MessageCreate(role="user", content="Test")
        assert "session_id" in str(exc_info.value)
    
    def test_session_id_uuid_validation(self):
        """Test session_id UUID validation."""
        # Valid UUID4 should work
        valid_uuid4 = uuid4()
        message = MessageCreate(
            role="user",
            content="Test",
            session_id=valid_uuid4
        )
        assert message.session_id == valid_uuid4
        
        # Invalid UUID should fail
        with pytest.raises(ValidationError):
            MessageCreate(
                role="user",
                content="Test",
                session_id="not-a-uuid"
            )
    
    def test_inherits_base_validation(self):
        """Test MessageCreate inherits MessageBase validation."""
        with pytest.raises(ValidationError):
            MessageCreate(
                role="invalid_role",
                content="Test",
                session_id=uuid4()
            )


class TestMessageUpdate:
    """Test MessageUpdate schema validation."""
    
    def test_valid_content_update(self):
        """Test valid content update."""
        data = {"content": "Updated content"}
        
        update = MessageUpdate(**data)
        assert update.content == "Updated content"
        assert update.message_metadata is None
    
    def test_valid_metadata_update(self):
        """Test valid metadata update."""
        metadata = {"updated": True, "version": 2}
        data = {"message_metadata": metadata}
        
        update = MessageUpdate(**data)
        assert update.content is None
        assert update.message_metadata == metadata
    
    def test_valid_full_update(self):
        """Test update with both fields."""
        metadata = {"updated": True}
        data = {
            "content": "Fully updated content",
            "message_metadata": metadata
        }
        
        update = MessageUpdate(**data)
        assert update.content == "Fully updated content"
        assert update.message_metadata == metadata
    
    def test_empty_update(self):
        """Test update with no fields."""
        update = MessageUpdate()
        assert update.content is None
        assert update.message_metadata is None
    
    def test_content_validation_when_provided(self):
        """Test content validation applies when content is provided."""
        with pytest.raises(ValidationError) as exc_info:
            MessageUpdate(content="")
        assert "at least 1 character" in str(exc_info.value)


class TestMessage:
    """Test Message schema validation."""
    
    def test_valid_message_response(self):
        """Test valid message response creation."""
        message_id = uuid4()
        session_id = uuid4()
        created_at = datetime.utcnow()
        
        data = {
            "id": message_id,
            "session_id": session_id,
            "role": "user",
            "content": "Test message response",
            "message_metadata": {"test": "data"},
            "created_at": created_at
        }
        
        message = Message(**data)
        assert message.id == message_id
        assert message.session_id == session_id
        assert message.role == "user"
        assert message.content == "Test message response"
        assert message.created_at == created_at
    
    def test_required_fields(self):
        """Test all required fields are present."""
        required_fields = ["id", "session_id", "role", "content", "created_at"]
        
        for field in required_fields:
            data = {
                "id": uuid4(),
                "session_id": uuid4(),
                "role": "user",
                "content": "Test",
                "created_at": datetime.utcnow()
            }
            del data[field]
            
            with pytest.raises(ValidationError) as exc_info:
                Message(**data)
            assert field in str(exc_info.value)
    
    def test_inherits_base_validation(self):
        """Test Message inherits MessageBase validation."""
        with pytest.raises(ValidationError):
            Message(
                id=uuid4(),
                session_id=uuid4(),
                role="invalid_role",
                content="Test",
                created_at=datetime.utcnow()
            )


class TestMessageList:
    """Test MessageList schema validation."""
    
    def test_valid_message_list(self):
        """Test valid message list response."""
        messages = [
            Message(
                id=uuid4(),
                session_id=uuid4(),
                role="user",
                content=f"Message {i}",
                created_at=datetime.utcnow(),
                message_metadata={}
            ) for i in range(3)
        ]
        
        data = {
            "messages": messages,
            "total": 3,
            "page": 1,
            "per_page": 10,
            "has_more": False
        }
        
        message_list = MessageList(**data)
        assert len(message_list.messages) == 3
        assert message_list.total == 3
        assert message_list.page == 1
        assert message_list.has_more is False
    
    def test_empty_message_list(self):
        """Test empty message list."""
        data = {
            "messages": [],
            "total": 0,
            "page": 1,
            "per_page": 10,
            "has_more": False
        }
        
        message_list = MessageList(**data)
        assert message_list.messages == []
        assert message_list.total == 0
    
    def test_pagination_fields(self):
        """Test pagination field validation."""
        data = {
            "messages": [],
            "total": 100,
            "page": 5,
            "per_page": 20,
            "has_more": True
        }
        
        message_list = MessageList(**data)
        assert message_list.total == 100
        assert message_list.page == 5
        assert message_list.per_page == 20
        assert message_list.has_more is True


class TestSendMessageRequest:
    """Test SendMessageRequest schema validation."""
    
    def test_valid_send_message_request(self):
        """Test valid send message request."""
        data = {
            "content": "Hello, I need help with something.",
            "model_parameters": {
                "temperature": 0.7,
                "max_tokens": 100,
                "top_p": 0.9
            }
        }
        
        request = SendMessageRequest(**data)
        assert request.content == "Hello, I need help with something."
        assert request.model_parameters["temperature"] == 0.7
    
    def test_minimal_send_message_request(self):
        """Test minimal send message request."""
        data = {"content": "Simple message"}
        
        request = SendMessageRequest(**data)
        assert request.content == "Simple message"
        assert request.model_parameters == {}  # Default empty dict
    
    def test_content_validation_empty(self):
        """Test content validation with empty string."""
        with pytest.raises(ValidationError) as exc_info:
            SendMessageRequest(content="")
        assert "at least 1 character" in str(exc_info.value)
    
    def test_content_validation_too_long(self):
        """Test content validation with too long string."""
        long_content = "x" * 4001
        with pytest.raises(ValidationError) as exc_info:
            SendMessageRequest(content=long_content)
        assert "at most 4000 characters" in str(exc_info.value)
    
    def test_content_validation_max_length(self):
        """Test content validation at maximum length."""
        max_content = "x" * 4000
        request = SendMessageRequest(content=max_content)
        assert len(request.content) == 4000
    
    def test_model_parameters_complex(self):
        """Test model parameters with complex data."""
        complex_params = {
            "temperature": 0.8,
            "max_tokens": 500,
            "stop_sequences": ["Human:", "AI:"],
            "presence_penalty": 0.1,
            "frequency_penalty": 0.2,
            "custom_settings": {
                "use_context": True,
                "context_window": 2000
            }
        }
        
        request = SendMessageRequest(
            content="Test with complex parameters",
            model_parameters=complex_params
        )
        assert request.model_parameters == complex_params


class TestSendMessageResponse:
    """Test SendMessageResponse schema validation."""
    
    def test_valid_send_message_response(self):
        """Test valid send message response."""
        session_id = uuid4()
        chat_id = uuid4()
        now = datetime.utcnow()
        
        user_message = Message(
            id=uuid4(),
            session_id=session_id,
            role="user",
            content="User question",
            created_at=now,
            message_metadata={}
        )
        
        assistant_message = Message(
            id=uuid4(),
            session_id=session_id,
            role="assistant",
            content="Assistant response",
            created_at=now,
            message_metadata={}
        )
        
        data = {
            "user_message": user_message,
            "assistant_message": assistant_message,
            "chat_id": chat_id,
            "message_count": 5
        }
        
        response = SendMessageResponse(**data)
        assert response.user_message.content == "User question"
        assert response.assistant_message.content == "Assistant response"
        assert response.chat_id == chat_id
        assert response.message_count == 5
    
    def test_required_fields(self):
        """Test all required fields are present."""
        required_fields = ["user_message", "assistant_message", "chat_id", "message_count"]
        
        base_data = {
            "user_message": Message(
                id=uuid4(), session_id=uuid4(), role="user",
                content="Test", created_at=datetime.utcnow()
            ),
            "assistant_message": Message(
                id=uuid4(), session_id=uuid4(), role="assistant",
                content="Test", created_at=datetime.utcnow()
            ),
            "chat_id": uuid4(),
            "message_count": 1
        }
        
        for field in required_fields:
            data = base_data.copy()
            del data[field]
            
            with pytest.raises(ValidationError) as exc_info:
                SendMessageResponse(**data)
            assert field in str(exc_info.value)


class TestMessageSearchRequest:
    """Test MessageSearchRequest schema validation."""
    
    def test_valid_search_request(self):
        """Test valid message search request."""
        data = {
            "query": "search term",
            "limit": 50,
            "offset": 20
        }
        
        request = MessageSearchRequest(**data)
        assert request.query == "search term"
        assert request.limit == 50
        assert request.offset == 20
    
    def test_minimal_search_request(self):
        """Test minimal search request with defaults."""
        data = {"query": "test"}
        
        request = MessageSearchRequest(**data)
        assert request.query == "test"
        assert request.limit == 20  # default
        assert request.offset == 0   # default
    
    def test_query_validation_empty(self):
        """Test query validation with empty string."""
        with pytest.raises(ValidationError) as exc_info:
            MessageSearchRequest(query="")
        assert "at least 1 character" in str(exc_info.value)
    
    def test_query_validation_too_long(self):
        """Test query validation with too long string."""
        long_query = "x" * 201
        with pytest.raises(ValidationError) as exc_info:
            MessageSearchRequest(query=long_query)
        assert "at most 200 characters" in str(exc_info.value)
    
    def test_limit_validation_bounds(self):
        """Test limit validation bounds."""
        # Too small
        with pytest.raises(ValidationError):
            MessageSearchRequest(query="test", limit=0)
        
        # Too large
        with pytest.raises(ValidationError):
            MessageSearchRequest(query="test", limit=101)
        
        # Valid boundaries
        request_min = MessageSearchRequest(query="test", limit=1)
        assert request_min.limit == 1
        
        request_max = MessageSearchRequest(query="test", limit=100)
        assert request_max.limit == 100
    
    def test_offset_validation_negative(self):
        """Test offset validation with negative value."""
        with pytest.raises(ValidationError):
            MessageSearchRequest(query="test", offset=-1)
        
        # Zero should be valid
        request = MessageSearchRequest(query="test", offset=0)
        assert request.offset == 0


class TestMessageSearchResponse:
    """Test MessageSearchResponse schema validation."""
    
    def test_valid_search_response(self):
        """Test valid message search response."""
        messages = [
            Message(
                id=uuid4(),
                session_id=uuid4(),
                role="user",
                content=f"Search result {i}",
                created_at=datetime.utcnow(),
                message_metadata={}
            ) for i in range(2)
        ]
        
        data = {
            "messages": messages,
            "total_matches": 25,
            "query": "search term"
        }
        
        response = MessageSearchResponse(**data)
        assert len(response.messages) == 2
        assert response.total_matches == 25
        assert response.query == "search term"
    
    def test_empty_search_response(self):
        """Test empty search response."""
        data = {
            "messages": [],
            "total_matches": 0,
            "query": "no results"
        }
        
        response = MessageSearchResponse(**data)
        assert response.messages == []
        assert response.total_matches == 0
        assert response.query == "no results"


class TestSystemMessageResponse:
    """Test SystemMessageResponse schema validation."""
    
    def test_valid_system_message_response(self):
        """Test valid system message response."""
        system_message = Message(
            id=uuid4(),
            session_id=uuid4(),
            role="system",
            content="System prompt updated",
            created_at=datetime.utcnow(),
            message_metadata={}
        )
        
        data = {
            "message": "System message has been set",
            "system_message": system_message,
            "chat_id": "test-chat-123"
        }
        
        response = SystemMessageResponse(**data)
        assert response.message == "System message has been set"
        assert response.system_message.role == "system"
        assert response.chat_id == "test-chat-123"
    
    def test_required_fields(self):
        """Test all required fields are present."""
        required_fields = ["message", "system_message", "chat_id"]
        
        base_data = {
            "message": "Test message",
            "system_message": Message(
                id=uuid4(), session_id=uuid4(), role="system",
                content="Test", created_at=datetime.utcnow()
            ),
            "chat_id": "test-chat"
        }
        
        for field in required_fields:
            data = base_data.copy()
            del data[field]
            
            with pytest.raises(ValidationError) as exc_info:
                SystemMessageResponse(**data)
            assert field in str(exc_info.value)


class TestSchemaInteractions:
    """Test interactions between different message schemas."""
    
    def test_message_lifecycle_schemas(self):
        """Test complete message lifecycle using different schemas."""
        session_id = uuid4()
        
        # 1. Create message request
        create_request = MessageCreate(
            role="user",
            content="Test message lifecycle",
            session_id=session_id,
            message_metadata={"test": "lifecycle"}
        )
        
        # 2. Message response
        message_response = Message(
            id=uuid4(),
            session_id=session_id,
            role=create_request.role,
            content=create_request.content,
            message_metadata=create_request.message_metadata,
            created_at=datetime.utcnow()
        )
        
        # 3. Update message
        update_request = MessageUpdate(
            content="Updated content",
            message_metadata={"test": "updated"}
        )
        
        # 4. List messages
        message_list = MessageList(
            messages=[message_response],
            total=1,
            page=1,
            per_page=10,
            has_more=False
        )
        
        # Verify the flow
        assert create_request.session_id == message_response.session_id
        assert update_request.content == "Updated content"
        assert len(message_list.messages) == 1
    
    def test_send_message_complete_flow(self):
        """Test complete send message flow."""
        # Send message request
        send_request = SendMessageRequest(
            content="How are you?",
            model_parameters={"temperature": 0.7}
        )
        
        session_id = uuid4()
        chat_id = uuid4()
        now = datetime.utcnow()
        
        # User and assistant messages
        user_message = Message(
            id=uuid4(),
            session_id=session_id,
            role="user",
            content=send_request.content,
            created_at=now,
            message_metadata={}
        )
        
        assistant_message = Message(
            id=uuid4(),
            session_id=session_id,
            role="assistant",
            content="I'm doing well, thank you!",
            created_at=now,
            message_metadata=send_request.model_parameters
        )
        
        # Send message response
        send_response = SendMessageResponse(
            user_message=user_message,
            assistant_message=assistant_message,
            chat_id=chat_id,
            message_count=2
        )
        
        # Verify the complete flow
        assert send_response.user_message.content == send_request.content
        assert send_response.assistant_message.role == "assistant"
        assert send_response.message_count == 2
