"""
Unit tests for settings schemas validation.

This module tests all settings-related Pydantic models to ensure proper validation,
serialization, and error handling.
"""

import pytest
from typing import Dict, Any
from uuid import uuid4
from datetime import datetime
from pydantic import ValidationError

from app.schemas.settings_schemas import (
    ChatSettingsBase, ChatSettingsCreate, ChatSettingsUpdate,
    ChatSettings, ChatSettingsResponse
)


class TestChatSettingsBase:
    """Test ChatSettingsBase schema validation."""
    
    def test_valid_settings_with_all_fields(self):
        """Test valid settings creation with all fields."""
        data = {
            "temperature": "0.8",
            "max_tokens": 2000,
            "system_prompt": "You are a helpful AI assistant."
        }
        
        settings = ChatSettingsBase(**data)
        assert settings.temperature == "0.8"
        assert settings.max_tokens == 2000
        assert settings.system_prompt == "You are a helpful AI assistant."
    
    def test_valid_settings_with_defaults(self):
        """Test settings creation with default values."""
        settings = ChatSettingsBase()
        assert settings.temperature == "0.7"  # default
        assert settings.max_tokens == 1000    # default
        assert settings.system_prompt is None # default
    
    def test_temperature_string_validation(self):
        """Test temperature accepts string values."""
        valid_temperatures = ["0.1", "0.7", "1.0", "1.5", "2.0"]
        
        for temp in valid_temperatures:
            settings = ChatSettingsBase(temperature=temp)
            assert settings.temperature == temp
    
    def test_max_tokens_validation_bounds(self):
        """Test max_tokens validation bounds."""
        # Valid boundaries
        settings_min = ChatSettingsBase(max_tokens=1)
        assert settings_min.max_tokens == 1
        
        settings_max = ChatSettingsBase(max_tokens=50000)
        assert settings_max.max_tokens == 50000
        
        # Too small
        with pytest.raises(ValidationError) as exc_info:
            ChatSettingsBase(max_tokens=0)
        assert "greater than or equal to 1" in str(exc_info.value)
        
        # Too large
        with pytest.raises(ValidationError) as exc_info:
            ChatSettingsBase(max_tokens=50001)
        assert "less than or equal to 50000" in str(exc_info.value)
    
    def test_max_tokens_validation_negative(self):
        """Test max_tokens validation with negative values."""
        with pytest.raises(ValidationError) as exc_info:
            ChatSettingsBase(max_tokens=-1)
        assert "greater than or equal to 1" in str(exc_info.value)
    
    def test_system_prompt_optional(self):
        """Test system_prompt is optional."""
        # None should be valid
        settings = ChatSettingsBase(system_prompt=None)
        assert settings.system_prompt is None
        
        # Empty string should be valid
        settings = ChatSettingsBase(system_prompt="")
        assert settings.system_prompt == ""
        
        # Non-empty string should be valid
        settings = ChatSettingsBase(system_prompt="Custom prompt")
        assert settings.system_prompt == "Custom prompt"
    
    def test_system_prompt_long_text(self):
        """Test system_prompt with long text."""
        long_prompt = "You are a very helpful assistant. " * 100
        settings = ChatSettingsBase(system_prompt=long_prompt)
        assert settings.system_prompt == long_prompt


class TestChatSettingsCreate:
    """Test ChatSettingsCreate schema validation."""
    
    def test_valid_settings_create(self):
        """Test valid settings creation request."""
        session_id = uuid4()
        data = {
            "session_id": session_id,
            "temperature": "0.9",
            "max_tokens": 1500,
            "system_prompt": "Be concise and helpful."
        }
        
        settings = ChatSettingsCreate(**data)
        assert settings.session_id == session_id
        assert settings.temperature == "0.9"
        assert settings.max_tokens == 1500
        assert settings.system_prompt == "Be concise and helpful."
    
    def test_minimal_settings_create(self):
        """Test minimal settings creation with only required field."""
        session_id = uuid4()
        data = {"session_id": session_id}
        
        settings = ChatSettingsCreate(**data)
        assert settings.session_id == session_id
        assert settings.temperature == "0.7"  # default
        assert settings.max_tokens == 1000    # default
        assert settings.system_prompt is None  # default
    
    def test_session_id_required(self):
        """Test session_id is required."""
        with pytest.raises(ValidationError) as exc_info:
            ChatSettingsCreate(temperature="0.8")
        assert "session_id" in str(exc_info.value)
    
    def test_session_id_uuid_validation(self):
        """Test session_id UUID validation."""
        # Valid UUID string should work
        settings = ChatSettingsCreate(
            session_id="123e4567-e89b-12d3-a456-426614174000"
        )
        assert settings.session_id is not None
        
        # Invalid UUID should fail
        with pytest.raises(ValidationError):
            ChatSettingsCreate(session_id="not-a-uuid")
    
    def test_inherits_base_validation(self):
        """Test ChatSettingsCreate inherits base validation."""
        session_id = uuid4()
        
        # Should inherit max_tokens validation
        with pytest.raises(ValidationError):
            ChatSettingsCreate(
                session_id=session_id,
                max_tokens=60000  # Too large
            )


class TestChatSettingsUpdate:
    """Test ChatSettingsUpdate schema validation."""
    
    def test_valid_partial_update(self):
        """Test valid partial update with some fields."""
        data = {
            "temperature": "0.5",
            "system_prompt": "Updated prompt"
        }
        
        update = ChatSettingsUpdate(**data)
        assert update.temperature == "0.5"
        assert update.system_prompt == "Updated prompt"
        assert update.max_tokens == 1000  # inherits default from base
    
    def test_empty_update(self):
        """Test update with no fields provided."""
        update = ChatSettingsUpdate()
        assert update.temperature == "0.7"  # inherits default from base
        assert update.max_tokens == 1000    # inherits default from base
        assert update.system_prompt is None # inherits default from base
    
    def test_single_field_updates(self):
        """Test updating single fields."""
        # Temperature only
        temp_update = ChatSettingsUpdate(temperature="1.2")
        assert temp_update.temperature == "1.2"
        assert temp_update.max_tokens == 1000  # inherits default
        assert temp_update.system_prompt is None  # inherits default
        
        # Max tokens only
        tokens_update = ChatSettingsUpdate(max_tokens=500)
        assert tokens_update.temperature == "0.7"  # inherits default
        assert tokens_update.max_tokens == 500
        assert tokens_update.system_prompt is None  # inherits default
        
        # System prompt only
        prompt_update = ChatSettingsUpdate(system_prompt="New prompt")
        assert prompt_update.temperature == "0.7"  # inherits default
        assert prompt_update.max_tokens == 1000    # inherits default
        assert prompt_update.system_prompt == "New prompt"
    
    def test_all_fields_update(self):
        """Test update with all fields provided."""
        data = {
            "temperature": "1.0",
            "max_tokens": 3000,
            "system_prompt": "Comprehensive update"
        }
        
        update = ChatSettingsUpdate(**data)
        assert update.temperature == "1.0"
        assert update.max_tokens == 3000
        assert update.system_prompt == "Comprehensive update"
    
    def test_validation_on_provided_fields(self):
        """Test validation applies to provided fields."""
        # Temperature validation (if any exists)
        temp_update = ChatSettingsUpdate(temperature="0.1")
        assert temp_update.temperature == "0.1"
        
        # Max tokens validation
        with pytest.raises(ValidationError):
            ChatSettingsUpdate(max_tokens=0)  # Too small
    
    def test_system_prompt_clear_to_none(self):
        """Test clearing system prompt to None."""
        update = ChatSettingsUpdate(system_prompt=None)
        assert update.system_prompt is None
    
    def test_system_prompt_clear_to_empty(self):
        """Test clearing system prompt to empty string."""
        update = ChatSettingsUpdate(system_prompt="")
        assert update.system_prompt == ""


class TestChatSettings:
    """Test ChatSettings schema validation."""
    
    def test_valid_settings_response(self):
        """Test valid settings response creation."""
        session_id = uuid4()
        created_at = datetime.utcnow()
        updated_at = datetime.utcnow()
        
        data = {
            "session_id": str(session_id),  # String for API response
            "temperature": "0.7",
            "max_tokens": 1000,
            "system_prompt": "You are helpful",
            "created_at": created_at,
            "updated_at": updated_at
        }
        
        settings = ChatSettings(**data)
        assert settings.session_id == str(session_id)
        assert settings.temperature == "0.7"
        assert settings.max_tokens == 1000
        assert settings.system_prompt == "You are helpful"
        assert settings.created_at == created_at
        assert settings.updated_at == updated_at
    
    def test_from_orm_class_method(self):
        """Test from_orm class method functionality."""
        # Create a mock database object
        class MockDBSettings:
            def __init__(self):
                self.session_id = uuid4()
                self.temperature = "0.8"
                self.max_tokens = 2000
                self.system_prompt = "Be helpful"
                self.created_at = datetime.utcnow()
                self.updated_at = datetime.utcnow()
        
        db_obj = MockDBSettings()
        settings = ChatSettings.from_orm(db_obj)
        
        assert settings.session_id == str(db_obj.session_id)  # Converted to string
        assert settings.temperature == db_obj.temperature
        assert settings.max_tokens == db_obj.max_tokens
        assert settings.system_prompt == db_obj.system_prompt
        assert settings.created_at == db_obj.created_at
        assert settings.updated_at == db_obj.updated_at
    
    def test_from_orm_with_none_values(self):
        """Test from_orm with None values."""
        class MockDBSettings:
            def __init__(self):
                self.session_id = uuid4()
                self.temperature = None
                self.max_tokens = 1000
                self.system_prompt = None
                self.created_at = datetime.utcnow()
                self.updated_at = datetime.utcnow()
        
        db_obj = MockDBSettings()
        settings = ChatSettings.from_orm(db_obj)
        
        assert settings.temperature is None
        assert settings.system_prompt is None
        assert settings.max_tokens == 1000
    
    def test_session_id_string_conversion(self):
        """Test session_id is stored as string in response."""
        session_id = uuid4()
        
        # Test with string session_id (schema expects string)
        data = {
            "session_id": str(session_id),  # Schema expects string
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # This should work with string session_id
        settings = ChatSettings(**data)
        assert isinstance(settings.session_id, str)
        assert settings.session_id == str(session_id)
    
    def test_required_timestamp_fields(self):
        """Test required timestamp fields."""
        required_fields = ["session_id", "created_at", "updated_at"]
        
        base_data = {
            "session_id": str(uuid4()),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        for field in required_fields:
            data = base_data.copy()
            del data[field]
            
            with pytest.raises(ValidationError) as exc_info:
                ChatSettings(**data)
            assert field in str(exc_info.value)
    
    def test_inherits_base_validation(self):
        """Test ChatSettings inherits base validation."""
        with pytest.raises(ValidationError):
            ChatSettings(
                session_id=str(uuid4()),
                temperature="0.7",
                max_tokens=60000,  # Too large
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )


class TestChatSettingsResponse:
    """Test ChatSettingsResponse schema validation."""
    
    def test_valid_settings_response(self):
        """Test valid settings response wrapper."""
        settings = ChatSettings(
            session_id=str(uuid4()),
            temperature="0.7",
            max_tokens=1000,
            system_prompt="Test prompt",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        data = {
            "settings": settings,
            "message": "Settings updated successfully"
        }
        
        response = ChatSettingsResponse(**data)
        assert response.settings == settings
        assert response.message == "Settings updated successfully"
    
    def test_default_message(self):
        """Test default success message."""
        settings = ChatSettings(
            session_id=str(uuid4()),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        response = ChatSettingsResponse(settings=settings)
        assert response.message == "Settings updated successfully"  # default
    
    def test_custom_message(self):
        """Test custom response message."""
        settings = ChatSettings(
            session_id=str(uuid4()),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        custom_message = "Settings created successfully"
        response = ChatSettingsResponse(
            settings=settings,
            message=custom_message
        )
        assert response.message == custom_message
    
    def test_settings_required(self):
        """Test settings field is required."""
        with pytest.raises(ValidationError) as exc_info:
            ChatSettingsResponse(message="Test message")
        assert "settings" in str(exc_info.value)


class TestSchemaInteractions:
    """Test interactions between different settings schemas."""
    
    def test_settings_lifecycle_schemas(self):
        """Test complete settings lifecycle using different schemas."""
        session_id = uuid4()
        
        # 1. Create settings request
        create_request = ChatSettingsCreate(
            session_id=session_id,
            temperature="0.8",
            max_tokens=1500,
            system_prompt="Initial prompt"
        )
        
        # 2. Settings response (after creation)
        settings_response = ChatSettings(
            session_id=str(session_id),  # API returns as string
            temperature=create_request.temperature,
            max_tokens=create_request.max_tokens,
            system_prompt=create_request.system_prompt,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # 3. Update settings
        update_request = ChatSettingsUpdate(
            temperature="0.9",
            system_prompt="Updated prompt"
            # max_tokens not updated
        )
        
        # 4. Updated settings response
        updated_settings = ChatSettings(
            session_id=str(session_id),
            temperature=update_request.temperature,  # updated
            max_tokens=settings_response.max_tokens,  # unchanged
            system_prompt=update_request.system_prompt,  # updated
            created_at=settings_response.created_at,  # unchanged
            updated_at=datetime.utcnow()  # new timestamp
        )
        
        # 5. Response wrapper
        response_wrapper = ChatSettingsResponse(
            settings=updated_settings,
            message="Settings updated successfully"
        )
        
        # Verify the flow
        assert str(create_request.session_id) == settings_response.session_id
        assert update_request.temperature == updated_settings.temperature
        assert settings_response.max_tokens == updated_settings.max_tokens  # unchanged
        assert response_wrapper.settings.system_prompt == "Updated prompt"
    
    def test_settings_inheritance_chain(self):
        """Test inheritance chain validation works correctly."""
        session_id = uuid4()
        
        # Base validation should work in all derived classes
        base_data = {
            "temperature": "0.7",
            "max_tokens": 1000,
            "system_prompt": "Test"
        }
        
        # Test base schema
        base_settings = ChatSettingsBase(**base_data)
        assert base_settings.temperature == "0.7"
        
        # Test create schema (adds session_id)
        create_data = {**base_data, "session_id": session_id}
        create_settings = ChatSettingsCreate(**create_data)
        assert create_settings.session_id == session_id
        
        # Test update schema (inherits defaults from base)
        update_settings = ChatSettingsUpdate(temperature="0.8")
        assert update_settings.temperature == "0.8"
        assert update_settings.max_tokens == 1000  # inherits default
        
        # Test response schema (adds timestamps)
        response_data = {
            **base_data,
            "session_id": str(session_id),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        response_settings = ChatSettings(**response_data)
        assert response_settings.session_id == str(session_id)
    
    def test_schema_validation_consistency(self):
        """Test validation is consistent across schemas."""
        # Invalid max_tokens should fail in all schemas
        invalid_max_tokens = 60000
        
        with pytest.raises(ValidationError):
            ChatSettingsBase(max_tokens=invalid_max_tokens)
        
        with pytest.raises(ValidationError):
            ChatSettingsCreate(
                session_id=uuid4(),
                max_tokens=invalid_max_tokens
            )
        
        with pytest.raises(ValidationError):
            ChatSettingsUpdate(max_tokens=invalid_max_tokens)
        
        with pytest.raises(ValidationError):
            ChatSettings(
                session_id=str(uuid4()),
                max_tokens=invalid_max_tokens,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
    
    def test_serialization_compatibility(self):
        """Test schemas can be properly serialized/deserialized."""
        session_id = uuid4()
        now = datetime.utcnow()
        
        # Create settings object
        settings = ChatSettings(
            session_id=str(session_id),
            temperature="0.7",
            max_tokens=1000,
            system_prompt="Test prompt",
            created_at=now,
            updated_at=now
        )
        
        # Test serialization
        serialized = settings.model_dump()
        assert serialized["session_id"] == str(session_id)
        assert serialized["temperature"] == "0.7"
        assert "created_at" in serialized
        
        # Test response wrapper serialization
        response = ChatSettingsResponse(settings=settings)
        response_serialized = response.model_dump()
        assert "settings" in response_serialized
        assert "message" in response_serialized
