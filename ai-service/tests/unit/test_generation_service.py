"""
Unit tests for GenerationService.

This module tests the GenerationService class to ensure proper response
generation, parameter handling, and error conditions.
"""

import pytest
from unittest.mock import AsyncMock, patch
from typing import List, Dict, Any

from app.services.generation_service import GenerationService
from app.schemas.ai_schemas import Message


class TestGenerationService:
    """Test GenerationService functionality."""
    
    @pytest.fixture
    def generation_service(self):
        """Create GenerationService instance for testing."""
        return GenerationService()
    
    @pytest.fixture
    def sample_messages(self) -> List[Message]:
        """Provide sample messages for testing."""
        return [
            Message(role="system", content="You are a helpful assistant."),
            Message(role="user", content="Hello, how are you?"),
            Message(role="assistant", content="I'm doing well, thank you!"),
            Message(role="user", content="What can you help me with?")
        ]
    
    @pytest.mark.asyncio
    async def test_generate_response_with_user_messages(self, generation_service, sample_messages):
        """Test response generation with user messages."""
        response = await generation_service.generate_response(
            model_id="test-model",
            messages=sample_messages,
            parameters={"temperature": 0.7}
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert "What can you help me with?" in response
    
    @pytest.mark.asyncio
    async def test_generate_response_no_user_messages(self, generation_service):
        """Test response generation with no user messages."""
        messages = [
            Message(role="system", content="You are a helpful assistant."),
            Message(role="assistant", content="I'm ready to help.")
        ]
        
        response = await generation_service.generate_response(
            model_id="test-model",
            messages=messages
        )
        
        assert response == "Hello! How can I help you today?"
    
    @pytest.mark.asyncio
    async def test_generate_response_empty_messages(self, generation_service):
        """Test response generation with empty messages list."""
        response = await generation_service.generate_response(
            model_id="test-model",
            messages=[]
        )
        
        assert response == "Hello! How can I help you today?"
    
    @pytest.mark.asyncio
    async def test_generate_response_with_parameters(self, generation_service, sample_messages):
        """Test response generation with various parameters."""
        parameters = {
            "temperature": 0.8,
            "max_tokens": 150,
            "top_p": 0.9
        }
        
        response = await generation_service.generate_response(
            model_id="test-model",
            messages=sample_messages,
            parameters=parameters
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
    
    @pytest.mark.asyncio
    async def test_generate_response_without_parameters(self, generation_service, sample_messages):
        """Test response generation without parameters."""
        response = await generation_service.generate_response(
            model_id="test-model",
            messages=sample_messages
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
    
    @pytest.mark.asyncio
    async def test_generate_response_different_models(self, generation_service, sample_messages):
        """Test response generation with different model IDs."""
        models = ["model-1", "model-2", "gpt-3.5-turbo", "claude-instant"]
        
        for model_id in models:
            response = await generation_service.generate_response(
                model_id=model_id,
                messages=sample_messages
            )
            
            assert isinstance(response, str)
            assert len(response) > 0
    
    @pytest.mark.asyncio
    async def test_generate_response_with_single_user_message(self, generation_service):
        """Test response generation with single user message."""
        messages = [Message(role="user", content="Tell me a joke")]
        
        response = await generation_service.generate_response(
            model_id="test-model",
            messages=messages
        )
        
        assert "Tell me a joke" in response
        assert "mock AI response" in response
    
    @pytest.mark.asyncio
    async def test_generate_response_with_long_message(self, generation_service):
        """Test response generation with long user message."""
        long_content = "This is a very long message. " * 50
        messages = [Message(role="user", content=long_content)]
        
        response = await generation_service.generate_response(
            model_id="test-model",
            messages=messages
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert long_content in response
    
    @pytest.mark.asyncio
    async def test_generate_response_with_special_characters(self, generation_service):
        """Test response generation with special characters in messages."""
        messages = [
            Message(role="user", content="Hello! 🤖 Can you help with JSON: {'key': 'value'}?")
        ]
        
        response = await generation_service.generate_response(
            model_id="test-model",
            messages=messages
        )
        
        assert "🤖" in response
        assert "JSON" in response
        assert "{'key': 'value'}" in response
    
    @pytest.mark.asyncio
    async def test_generate_response_conversation_history(self, generation_service):
        """Test response generation with conversation history."""
        messages = [
            Message(role="user", content="What's 2+2?"),
            Message(role="assistant", content="2+2 equals 4."),
            Message(role="user", content="What about 3+3?"),
            Message(role="assistant", content="3+3 equals 6."),
            Message(role="user", content="Thank you!")
        ]
        
        response = await generation_service.generate_response(
            model_id="test-model",
            messages=messages
        )
        
        assert "Thank you!" in response
        assert isinstance(response, str)
    
    @pytest.mark.asyncio
    async def test_generate_response_error_handling(self, generation_service):
        """Test error handling in response generation."""
        messages = [Message(role="user", content="Hello")]
        
        # Test with invalid parameters that might cause errors
        with patch('app.services.generation_service.logger') as mock_logger:
            try:
                response = await generation_service.generate_response(
                    model_id="test-model",
                    messages=messages,
                    parameters={"invalid_param": "invalid_value"}
                )
                # Should still return a response even with invalid params
                assert isinstance(response, str)
            except Exception as e:
                # If an exception is raised, ensure it's logged
                mock_logger.error.assert_called()
                raise e
    
    @pytest.mark.asyncio  
    async def test_generate_response_with_system_message(self, generation_service):
        """Test response generation with system message."""
        messages = [
            Message(role="system", content="You are a helpful math tutor."),
            Message(role="user", content="Explain algebra")
        ]
        
        response = await generation_service.generate_response(
            model_id="test-model",
            messages=messages
        )
        
        assert "Explain algebra" in response
        assert isinstance(response, str)
    
    @pytest.mark.asyncio
    async def test_generate_response_logging(self, generation_service, sample_messages):
        """Test that response generation produces appropriate logs."""
        with patch('app.services.generation_service.logger') as mock_logger:
            await generation_service.generate_response(
                model_id="test-model",
                messages=sample_messages,
                parameters={"temperature": 0.7}
            )
            
            # Check that debug logs were called
            assert mock_logger.debug.call_count >= 2
            
            # Check log content
            debug_calls = [call.args[0] for call in mock_logger.debug.call_args_list]
            assert any("Starting generation" in call for call in debug_calls)
            assert any("Generation completed" in call for call in debug_calls)
    
    def test_init(self):
        """Test GenerationService initialization."""
        service = GenerationService()
        assert isinstance(service, GenerationService)
    
    @pytest.mark.asyncio
    async def test_generate_response_return_type(self, generation_service, sample_messages):
        """Test that generate_response always returns a string."""
        response = await generation_service.generate_response(
            model_id="test-model", 
            messages=sample_messages
        )
        
        assert isinstance(response, str)
        assert len(response) > 0


class TestGenerationServiceEdgeCases:
    """Test edge cases and error conditions for GenerationService."""
    
    @pytest.fixture
    def generation_service(self):
        """Create GenerationService instance for testing."""
        return GenerationService()
    
    @pytest.mark.asyncio
    async def test_generate_response_with_none_parameters(self, generation_service):
        """Test response generation with None parameters."""
        messages = [Message(role="user", content="Hello")]
        
        response = await generation_service.generate_response(
            model_id="test-model",
            messages=messages,
            parameters=None
        )
        
        assert isinstance(response, str)
    
    @pytest.mark.asyncio
    async def test_generate_response_with_empty_content(self, generation_service):
        """Test response generation with empty message content."""
        messages = [Message(role="user", content="")]
        
        response = await generation_service.generate_response(
            model_id="test-model",
            messages=messages
        )
        
        # Should include the empty content in the response
        assert isinstance(response, str)
        assert "mock AI response" in response
    
    @pytest.mark.asyncio
    async def test_generate_response_whitespace_only_content(self, generation_service):
        """Test response generation with whitespace-only content."""
        messages = [Message(role="user", content="   ")]
        
        response = await generation_service.generate_response(
            model_id="test-model",
            messages=messages
        )
        
        assert isinstance(response, str)
        assert "   " in response
    
    @pytest.mark.asyncio
    async def test_generate_response_unicode_content(self, generation_service):
        """Test response generation with unicode content."""
        messages = [Message(role="user", content="こんにちは! مرحبا! Hello! 🌍")]
        
        response = await generation_service.generate_response(
            model_id="test-model",
            messages=messages
        )
        
        assert "こんにちは!" in response
        assert "مرحبا!" in response
        assert "🌍" in response
    
    @pytest.mark.asyncio
    async def test_generate_response_very_long_model_id(self, generation_service):
        """Test response generation with very long model ID."""
        messages = [Message(role="user", content="Test")]
        long_model_id = "a" * 1000  # Very long model ID
        
        response = await generation_service.generate_response(
            model_id=long_model_id,
            messages=messages
        )
        
        assert isinstance(response, str)
