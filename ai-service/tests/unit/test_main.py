"""
Unit tests for FastAPI main application endpoints.

This module tests the main FastAPI application endpoints to ensure proper
request handling, response formats, and error conditions.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any

from app.main import app
from app.schemas.ai_schemas import Message


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test successful health check."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "AI Inference Service"
    
    @pytest.mark.asyncio
    async def test_health_check_response_format(self):
        """Test health check response format."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "status" in data
        assert "service" in data
        assert len(data) == 2


class TestGenerateEndpoint:
    """Test text generation endpoint."""
    
    @pytest.fixture
    def sample_request_data(self):
        """Provide sample request data for testing."""
        return {
            "model": "test-model",
            "messages": [
                {"role": "user", "content": "Hello, how are you?"}
            ],
            "parameters": {"temperature": 0.7, "max_tokens": 100}
        }
    
    @pytest.fixture
    def sample_request_data_no_model(self):
        """Provide sample request data without model for testing."""
        return {
            "messages": [
                {"role": "user", "content": "Hello, how are you?"}
            ],
            "parameters": {"temperature": 0.7}
        }
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self, sample_request_data):
        """Test successful response generation."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/generate", json=sample_request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "response" in data
        assert "model" in data
        assert "usage" in data
        assert isinstance(data["response"], str)
        assert data["model"] == "test-model"
        assert "Hello, how are you?" in data["response"]
    
    @pytest.mark.asyncio
    async def test_generate_response_without_model(self, sample_request_data_no_model):
        """Test response generation without model specified."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/generate", json=sample_request_data_no_model)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "response" in data
        assert data["model"] == "default"
        assert isinstance(data["response"], str)
    
    @pytest.mark.asyncio
    async def test_generate_response_empty_messages(self):
        """Test response generation with empty messages."""
        request_data = {
            "model": "test-model",
            "messages": []
        }
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/generate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["response"], str)
    
    @pytest.mark.asyncio
    async def test_generate_response_multiple_messages(self):
        """Test response generation with multiple messages."""
        request_data = {
            "model": "test-model",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello!"},
                {"role": "assistant", "content": "Hi there!"},
                {"role": "user", "content": "How are you?"}
            ],
            "parameters": {"temperature": 0.8}
        }
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/generate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data["response"], str)
        assert "How are you?" in data["response"]
    
    @pytest.mark.asyncio
    async def test_generate_response_with_system_message(self):
        """Test response generation with system message."""
        request_data = {
            "model": "test-model",
            "messages": [
                {"role": "system", "content": "You are a helpful math tutor."},
                {"role": "user", "content": "Explain fractions"}
            ]
        }
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/generate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "Explain fractions" in data["response"]
    
    @pytest.mark.asyncio
    async def test_generate_response_various_parameters(self):
        """Test response generation with various parameters."""
        request_data = {
            "model": "test-model",
            "messages": [{"role": "user", "content": "Test"}],
            "parameters": {
                "temperature": 0.9,
                "max_tokens": 200,
                "top_p": 0.95,
                "frequency_penalty": 0.1
            }
        }
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/generate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["response"], str)
    
    @pytest.mark.asyncio
    async def test_generate_response_missing_required_field(self):
        """Test response generation with missing required field."""
        request_data = {
            "model": "test-model"
            # Missing messages field
        }
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/generate", json=request_data)
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_generate_response_invalid_message_format(self):
        """Test response generation with invalid message format."""
        request_data = {
            "model": "test-model",
            "messages": [
                {"role": "user"}  # Missing content
            ]
        }
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/generate", json=request_data)
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_generate_response_usage_calculation(self, sample_request_data):
        """Test that usage statistics are calculated correctly."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/generate", json=sample_request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        usage = data["usage"]
        assert isinstance(usage["prompt_tokens"], int)
        assert isinstance(usage["completion_tokens"], int)
        assert isinstance(usage["total_tokens"], int)
        assert usage["total_tokens"] == usage["prompt_tokens"] + usage["completion_tokens"]
    
    @pytest.mark.asyncio
    async def test_generate_response_with_special_characters(self):
        """Test response generation with special characters."""
        request_data = {
            "model": "test-model",
            "messages": [
                {"role": "user", "content": "Hello! 🤖 JSON: {'key': 'value'}"}
            ]
        }
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/generate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "🤖" in data["response"]
        assert "JSON" in data["response"]


class TestChatEndpoint:
    """Test chat completion endpoint."""
    
    @pytest.mark.asyncio
    async def test_chat_completion_success(self):
        """Test successful chat completion."""
        request_data = {
            "model": "test-model",
            "messages": [
                {"role": "user", "content": "Hello, how are you?"}
            ],
            "parameters": {"temperature": 0.7}
        }
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/chat", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "response" in data
        assert "model" in data
        assert "usage" in data
        assert isinstance(data["response"], str)
    
    @pytest.mark.asyncio
    async def test_chat_completion_same_as_generate(self):
        """Test that chat completion produces same result as generate."""
        request_data = {
            "model": "test-model",
            "messages": [
                {"role": "user", "content": "Test message"}
            ]
        }
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            generate_response = await client.post("/generate", json=request_data)
            chat_response = await client.post("/chat", json=request_data)
        
        assert generate_response.status_code == 200
        assert chat_response.status_code == 200
        
        # Both endpoints should return the same structure
        generate_data = generate_response.json()
        chat_data = chat_response.json()
        
        assert generate_data["model"] == chat_data["model"]
        assert "response" in generate_data
        assert "response" in chat_data
        assert "usage" in generate_data
        assert "usage" in chat_data


class TestApplicationSetup:
    """Test application configuration and setup."""
    
    def test_app_title_and_version(self):
        """Test application title and version."""
        assert app.title == "AI Inference Service"
        assert app.version == "1.0.0"
        assert "AI model inference and management" in app.description
    
    @pytest.mark.asyncio
    async def test_cors_configuration(self):
        """Test CORS configuration."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Test preflight request
            response = await client.options(
                "/health",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET"
                }
            )
        
        # Should not return error due to CORS
        assert response.status_code in [200, 404]  # 404 if OPTIONS not explicitly handled
    
    @pytest.mark.asyncio
    async def test_root_path_not_found(self):
        """Test that root path returns 404."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/")
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_nonexistent_endpoint(self):
        """Test accessing non-existent endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/nonexistent")
        
        assert response.status_code == 404


class TestErrorHandling:
    """Test error handling in endpoints."""
    
    @pytest.mark.asyncio
    async def test_invalid_json(self):
        """Test handling of invalid JSON."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/generate",
                content="invalid json",
                headers={"Content-Type": "application/json"}
            )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_empty_request_body(self):
        """Test handling of empty request body."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/generate", json={})
        
        assert response.status_code == 422  # Missing required fields
    
    @pytest.mark.asyncio
    async def test_wrong_http_method(self):
        """Test using wrong HTTP method."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Try GET on POST endpoint
            response = await client.get("/generate")
        
        assert response.status_code == 405  # Method not allowed
    
    @pytest.mark.asyncio
    async def test_large_request_body(self):
        """Test handling of large request body."""
        # Create a very large message
        large_content = "x" * 100000  # 100KB message
        request_data = {
            "model": "test-model",
            "messages": [
                {"role": "user", "content": large_content}
            ]
        }
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/generate", json=request_data)
        
        # Should handle large requests gracefully
        assert response.status_code in [200, 413, 422]  # Success, too large, or validation error


class TestLogging:
    """Test logging behavior in endpoints."""
    
    @pytest.mark.asyncio
    async def test_generate_endpoint_logging(self):
        """Test that generate endpoint produces appropriate logs."""
        request_data = {
            "model": "test-model",
            "messages": [{"role": "user", "content": "Test"}],
            "parameters": {"temperature": 0.7}
        }
        
        with patch('app.main.logger') as mock_logger:
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post("/generate", json=request_data)
            
            assert response.status_code == 200
            
            # Check that debug logs were called
            assert mock_logger.debug.call_count >= 1
            
            # Check for specific log messages
            debug_calls = [call.args[0] for call in mock_logger.debug.call_args_list]
            assert any("Generation request received" in call for call in debug_calls)
    
    @pytest.mark.asyncio 
    async def test_error_logging(self):
        """Test that errors are properly logged."""
        # Mock the generation service to raise an exception
        with patch('app.main.generation_service.generate_response') as mock_generate:
            mock_generate.side_effect = Exception("Test error")
            
            with patch('app.main.logger') as mock_logger:
                request_data = {
                    "model": "test-model", 
                    "messages": [{"role": "user", "content": "Test"}]
                }
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.post("/generate", json=request_data)
                
                assert response.status_code == 500
                mock_logger.error.assert_called()
                
                # Check error message content
                error_call = mock_logger.error.call_args[0][0]
                assert "Error generating response" in error_call
