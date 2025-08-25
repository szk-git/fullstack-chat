"""
Global test configuration and fixtures for API Service testing.

This module provides reusable fixtures and configuration for all tests
while maintaining strict isolation between test cases.
"""

import os
# Set test environment variables before importing app modules
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Dict, Any, List
import uuid
from datetime import datetime

from app.main import app
from app.core.database import get_db
from app.repositories.chat_repository import ChatRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.settings_repository import ChatSettingsRepository
from app.services.ai_client import AIServiceClient
from app.services.chat_service import ChatService


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_db_session():
    """
    Create a mock database session for testing.
    
    This fixture provides a fully mocked SQLAlchemy session that can be
    used to test repository operations without touching a real database.
    """
    session = MagicMock()
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.close = MagicMock()
    session.add = MagicMock()
    session.delete = MagicMock()
    session.query = MagicMock()
    session.execute = MagicMock()
    session.refresh = MagicMock()
    return session


@pytest.fixture
def mock_chat_repository():
    """Mock ChatRepository for testing service layer."""
    repo = MagicMock(spec=ChatRepository)
    
    # Mock return values
    repo.create_chat_session = AsyncMock(return_value=MagicMock(id=uuid.uuid4()))
    repo.get_chat_session_by_id = AsyncMock(return_value=None)
    repo.get_chat_sessions_by_session_id = AsyncMock(return_value=[])
    repo.update_chat_session = AsyncMock(return_value=MagicMock())
    repo.delete_chat_session = AsyncMock(return_value=True)
    repo.archive_chat_session = AsyncMock(return_value=MagicMock())
    
    return repo


@pytest.fixture
def mock_message_repository():
    """Mock MessageRepository for testing service layer."""
    repo = MagicMock(spec=MessageRepository)
    
    repo.create_message = AsyncMock(return_value=MagicMock(id=uuid.uuid4()))
    repo.get_messages_by_session = AsyncMock(return_value=[])
    repo.get_message_count = AsyncMock(return_value=0)
    
    return repo


@pytest.fixture
def mock_settings_repository():
    """Mock ChatSettingsRepository for testing service layer."""
    repo = MagicMock(spec=ChatSettingsRepository)
    
    repo.create_settings = AsyncMock(return_value=MagicMock())
    repo.get_settings_by_session = AsyncMock(return_value=None)
    repo.update_settings = AsyncMock(return_value=MagicMock())
    
    return repo


@pytest.fixture
def mock_ai_client():
    """Mock AIServiceClient for testing."""
    client = MagicMock(spec=AIServiceClient)
    
    # Mock async methods
    client.health_check = AsyncMock(return_value={"status": "healthy", "loaded_models": ["test-model"]})
    client.list_models = AsyncMock(return_value=[{"id": "test-model", "name": "Test Model"}])
    client.get_model_status = AsyncMock(return_value={"status": "loaded"})
    client.load_model = AsyncMock(return_value={"status": "loaded"})
    client.unload_model = AsyncMock(return_value={"status": "unloaded"})
    client.generate_response = AsyncMock(return_value="Test AI response")
    client.chat_completion = AsyncMock(return_value={
        "response": "Test AI response",
        "model": "test-model",
        "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
    })
    
    return client


@pytest.fixture
def mock_chat_service():
    """Mock ChatService for testing API endpoints."""
    service = MagicMock(spec=ChatService)
    
    # Mock service methods
    service.create_chat_session = AsyncMock(return_value=MagicMock(id=uuid.uuid4()))
    service.get_chat_sessions = AsyncMock(return_value=[])
    service.get_chat_session_by_id = AsyncMock(return_value=None)
    service.update_chat_session = AsyncMock(return_value=MagicMock())
    service.delete_chat_session = AsyncMock(return_value=True)
    service.send_message = AsyncMock(return_value=MagicMock())
    service.get_messages = AsyncMock(return_value=[])
    service.update_chat_settings = AsyncMock(return_value=MagicMock())
    
    return service


@pytest.fixture
def sample_chat_session_data():
    """Sample chat session data for testing."""
    return {
        "id": uuid.uuid4(),
        "session_id": "test-session-123",
        "title": "Test Chat Session",
        "model_name": "facebook/blenderbot-400M-distill",
        "is_archived": False,
        "is_pinned": False,
        "message_count": 0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "last_message_at": None
    }


@pytest.fixture
def sample_message_data():
    """Sample message data for testing."""
    return {
        "id": uuid.uuid4(),
        "session_id": uuid.uuid4(),
        "role": "user",
        "content": "Hello, how are you?",
        "message_metadata": {},
        "created_at": datetime.utcnow()
    }


@pytest.fixture
def sample_settings_data():
    """Sample settings data for testing."""
    return {
        "session_id": uuid.uuid4(),
        "temperature": "0.7",
        "max_tokens": 1000,
        "system_prompt": "You are a helpful assistant.",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def override_get_db(mock_db_session):
    """Override the get_db dependency with mock session."""
    def _override_get_db():
        yield mock_db_session
    
    return _override_get_db


@pytest.fixture
def test_client(override_get_db):
    """
    Create a test client for FastAPI testing.
    
    This fixture provides a test client with mocked database dependency.
    """
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    # Clean up dependency overrides
    app.dependency_overrides.clear()


@pytest.fixture
async def async_client(override_get_db):
    """
    Create an async HTTP client for testing FastAPI endpoints.
    """
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def reset_mocks():
    """
    Reset all mocks between tests to ensure clean state.
    """
    yield
    # Any cleanup logic can go here


class MockHTTPXResponse:
    """Mock HTTPX response for testing HTTP clients."""
    
    def __init__(self, json_data: Dict[str, Any], status_code: int = 200):
        self.json_data = json_data
        self.status_code = status_code
        self.headers = {}
        self.text = ""
    
    def json(self):
        return self.json_data
    
    def raise_for_status(self):
        if self.status_code >= 400:
            from httpx import HTTPStatusError, Request, Response
            request = Request("GET", "http://test")
            response = Response(self.status_code, request=request)
            raise HTTPStatusError("HTTP error", request=request, response=response)


@pytest.fixture
def mock_httpx_response():
    """Factory for creating mock HTTPX responses."""
    return MockHTTPXResponse
