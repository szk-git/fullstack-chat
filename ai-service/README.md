# AI Inference Service

FastAPI microservice for AI text generation and model inference.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start development server
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

Access at: [http://localhost:8001](http://localhost:8001)
Docs at: [http://localhost:8001/docs](http://localhost:8001/docs)

## Features

- **AI text generation** with multiple model support
- **Chat completion** endpoint for conversational AI
- **Configurable parameters** (temperature, max tokens)
- **Health monitoring** and model status
- **Model preloading** for Docker deployments
- **Async processing** with FastAPI

## Tech Stack

- **FastAPI** with async support
- **Transformers** for AI model handling
- **Pydantic** for data validation
- **Uvicorn** ASGI server
- **PyTorch** for model inference

## Project Structure

```
app/
├── main.py               # FastAPI application and routes
├── schemas/              # Pydantic data models
└── services/             # Business logic services
```

## API Endpoints

- `GET /health` - Service health and model status
- `POST /generate` - Generate AI responses
- `POST /chat` - Chat completion (alias for generate)

### Request Format
```json
{
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "parameters": {
    "temperature": 0.7,
    "max_tokens": 100
  }
}
```

## Testing

```bash
# Run all tests
pytest tests/unit/

# Run with coverage
pytest tests/unit/ --cov=app --cov-report=term-missing
```

## Model Preloading

For Docker deployments, models are preloaded during build:

```bash
# Configure models (optional)
export DEFAULT_MODELS="gpt2,microsoft/DialoGPT-small"
python preload_models.py
```

## Development

The service provides AI inference capabilities for the chat application. Models are loaded on-demand and cached for performance.

For the complete application setup, see the main project README.
