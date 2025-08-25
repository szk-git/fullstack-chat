# Chat API Service

FastAPI backend for the fullstack chat application with AI integration.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start development server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Access at: [http://localhost:8000](http://localhost:8000)
Docs at: [http://localhost:8000/docs](http://localhost:8000/docs)

## Features

- **Session-based chat management** with no authentication required
- **Message handling** with AI response generation
- **Chat organization** (pin, archive, search, filter)
- **AI model integration** with configurable parameters
- **Health monitoring** and comprehensive logging
- **Database support** (PostgreSQL/SQLite)

## Tech Stack

- **FastAPI** with async support
- **SQLAlchemy** ORM with PostgreSQL/SQLite
- **Pydantic** for data validation
- **HTTPX** for AI service communication
- **Uvicorn** ASGI server

## Project Structure

```
app/
├── api/v1/           # REST API endpoints
├── core/             # Database configuration
├── database/         # SQLAlchemy models
├── repositories/     # Data access layer
├── schemas/          # Pydantic schemas
├── services/         # Business logic
└── main.py           # Application entry point
```

## Environment Variables

```env
DATABASE_URL=postgresql://chatuser:chatpass@localhost:5432/chatdb
AI_SERVICE_URL=http://localhost:8001
CORS_ORIGINS=http://localhost:5173
DEBUG=true
```

## Key Endpoints

- `GET /api/v1/health` - Health check
- `GET /api/v1/chats` - List chat sessions
- `POST /api/v1/chats` - Create new chat
- `POST /api/v1/chats/{id}/messages` - Send message
- `GET /api/v1/models` - List AI models

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

## Development

The API uses session-based architecture with `X-Session-ID` headers for conversation isolation. Database tables are auto-created on startup.

For the complete application setup, see the main project README.
