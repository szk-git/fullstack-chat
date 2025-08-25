# Fullstack Chat Application

A modern chat application with AI integration featuring FastAPI backend, AI service, and React frontend.

## Components

### API Service
FastAPI backend with PostgreSQL database handling chat sessions, message storage, and communication with AI service.

### AI Service
Dedicated service for AI model inference using Hugging Face transformers (BlenderBot, DialoGPT).

### Frontend
React application with modern chat interface, theme switching, and real-time messaging capabilities.

### Database
PostgreSQL database for persistent storage of chat sessions, messages, and user preferences.

## Quick Start

**Start all services with Docker:**
```bash
docker compose up --build
```

**Access points:**
- Frontend: http://localhost:5173
- API: http://localhost:8000
- AI Service: http://localhost:8001
- API Documentation: http://localhost:8000/docs

## Docker Setup

The application uses Docker Compose to orchestrate all services:

- **PostgreSQL**: Database service with persistent volume
- **API Service**: FastAPI backend with automatic migrations
- **AI Service**: AI inference service with model caching
- **Frontend**: React development server with hot reload

All services are configured with proper networking and health checks.

## Development Setup

**Individual service development:**

```bash
# Start database only
docker compose up postgres -d

# API Service
cd api-service
pip install -r requirements.txt
export DATABASE_URL="postgresql://chatuser:chatpass@localhost:5432/chatdb"
export AI_SERVICE_URL="http://localhost:8001"
uvicorn app.main:app --reload --port 8000

# AI Service
cd ai-service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001

# Frontend
cd frontend
npm install
npm run dev
```

## Environment Variables

**API Service:**
```env
DATABASE_URL=postgresql://chatuser:chatpass@localhost:5432/chatdb
AI_SERVICE_URL=http://localhost:8001
CORS_ORIGINS=http://localhost:5173
```

**Frontend:**
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## Project Structure

```
fullstack-chat/
├── api-service/          # FastAPI backend
├── ai-service/           # AI inference service
├── frontend/             # React frontend
├── docker-compose.yml    # Service orchestration
└── README.md
```

## Features

- **Session-based chat management** with persistent storage
- **Multiple AI models** support (BlenderBot, DialoGPT)
- **Modern React interface** with dark/light theme toggle
- **Mobile-responsive design** with collapsible sidebar
- **Chat organization** (search, filter, pin, archive)
- **Real-time messaging** with proper error handling

## Key Commands

```bash
docker compose up --build    # Start all services
docker compose down          # Stop services
docker compose logs -f       # View logs
docker compose ps            # Check status
```

For detailed component information, see individual README files in each service directory.
