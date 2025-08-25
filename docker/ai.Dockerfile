# Multi-stage build for AI service
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TRANSFORMERS_CACHE=/app/.cache
ENV MODEL_CACHE_DIR=/app/models
ENV HF_HOME=/app/.cache
ENV HF_HUB_CACHE=/app/.cache/hub

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app directory and user first
WORKDIR /app
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Create cache directories with proper permissions
RUN mkdir -p /app/models /app/.cache /app/.cache/hub && \
    chown -R appuser:appuser /app

# Copy requirements first for better caching
COPY ai-service/requirements.txt .
RUN chown appuser:appuser requirements.txt

# Install Python dependencies
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu && \
    pip3 install --no-cache-dir -r requirements.txt

# Copy application code and preload script
COPY ai-service/app ./app
COPY ai-service/preload_models.py ./preload_models.py
RUN chown -R appuser:appuser ./app ./preload_models.py

# Switch to non-root user
USER appuser

# Pre-download models to avoid runtime issues
RUN python3 ./preload_models.py

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Expose port
EXPOSE 8001

# Command to run the application
CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
