"""
Global test configuration and fixtures for AI Service testing.

This module provides reusable fixtures and configuration for all tests
while maintaining strict isolation between test cases.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient
from typing import Dict, Any, List

# Import after setting up the test environment
from app.main import app
from app.services.generation_service import GenerationService
from app.schemas.ai_schemas import Message


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_model_loader():
    """
    Create a mock ModelLoader for testing (deprecated - kept for compatibility).
    """
    loader = MagicMock()
    
    # Mock basic properties for backward compatibility
    loader.loaded_models = {}
    loader.current_model = None
    
    # Mock methods with default return values
    loader.list_loaded_models.return_value = {}
    loader.get_available_models.return_value = {}
    loader.get_memory_usage.return_value = 0.0
    
    return loader


@pytest.fixture
def mock_generation_service():
    """
    Create a mock GenerationService for testing without model inference.
    """
    service = MagicMock(spec=GenerationService)
    service.generate_response = AsyncMock(return_value="Test response")
    return service


@pytest.fixture
def sample_messages() -> List[Message]:
    """
    Provide sample messages for testing conversation flows.
    """
    return [
        Message(role="system", content="You are a helpful assistant."),
        Message(role="user", content="Hello, how are you?"),
        Message(role="assistant", content="I'm doing well, thank you!"),
        Message(role="user", content="What's the weather like?")
    ]


@pytest.fixture
def sample_generation_parameters() -> Dict[str, Any]:
    """
    Provide sample generation parameters for testing.
    """
    return {
        "temperature": 0.7,
        "max_length": 100,
        "do_sample": True,
        "top_p": 0.9
    }


@pytest.fixture
async def async_client():
    """
    Create an async HTTP client for testing FastAPI endpoints.
    
    This fixture provides a test client that can be used to make
    HTTP requests to the FastAPI application.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_torch():
    """
    Mock torch operations to prevent actual GPU/CPU model operations.
    """
    with patch('torch.cuda.is_available', return_value=False):
        with patch('torch.no_grad'):
            yield


@pytest.fixture
def mock_transformers():
    """
    Mock transformers model loading to prevent downloading models.
    """
    mock_model = MagicMock()
    mock_model.generate.return_value = MagicMock()
    mock_model.config.max_position_embeddings = 1024
    
    mock_tokenizer = MagicMock()
    mock_tokenizer.encode.return_value = MagicMock()
    mock_tokenizer.decode.return_value = "Mocked response"
    mock_tokenizer.eos_token = "</s>"
    mock_tokenizer.pad_token = "</s>"
    mock_tokenizer.eos_token_id = 1
    
    with patch('transformers.AutoModelForCausalLM.from_pretrained', return_value=mock_model):
        with patch('transformers.AutoTokenizer.from_pretrained', return_value=mock_tokenizer):
            with patch('transformers.BlenderbotForConditionalGeneration.from_pretrained', return_value=mock_model):
                with patch('transformers.BlenderbotTokenizer.from_pretrained', return_value=mock_tokenizer):
                    yield mock_model, mock_tokenizer


@pytest.fixture
def app_with_mocked_dependencies(mock_model_loader, mock_generation_service):
    """
    Create app instance with mocked dependencies for testing.
    """
    with patch('app.main.model_loader', mock_model_loader):
        with patch('app.main.generation_service', mock_generation_service):
            yield app


@pytest.fixture(autouse=True)
def reset_logging():
    """
    Reset logging configuration between tests to ensure clean state.
    """
    import logging
    # Clear all loggers
    loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
    for logger in loggers:
        logger.handlers = []
        logger.level = logging.NOTSET
        logger.propagate = True
    
    yield
    
    # Cleanup after test
    for logger in loggers:
        logger.handlers = []


@pytest.fixture
def temp_directory(tmp_path):
    """
    Provide a temporary directory for test files.
    """
    return tmp_path


class MockResponse:
    """Mock HTTP response for testing external API calls."""
    
    def __init__(self, json_data: Dict[str, Any], status_code: int = 200):
        self.json_data = json_data
        self.status_code = status_code
        self.headers = {}
    
    def json(self):
        return self.json_data
    
    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


@pytest.fixture
def mock_http_responses():
    """Factory for creating mock HTTP responses."""
    return MockResponse
