from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import os
import uuid
from typing import List

from .core.database import init_db, check_db_connection
from .api.v1 import chats, models
from .services.ai_client import get_ai_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("Starting API service...")
    
    # Initialize database
    try:
        init_db()
        if not check_db_connection():
            raise Exception("Database connection failed")
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise e
    
    # Check AI service connection
    try:
        ai_client = get_ai_client()
        await ai_client.health_check()
        logger.info("AI service connection verified")
    except Exception as e:
        logger.warning(f"AI service connection failed: {e}")
    
    yield
    
    # Cleanup
    logger.info("Shutting down API service...")


app = FastAPI(
    title="Fullstack Chat API",
    version="2.0.0",
    description="Enhanced chat API with multi-session support, AI integration, and user management",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Health check endpoint
@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "version": "2.0.0",
        "database": "unknown",
        "ai_service": "unknown"
    }
    
    # Check database
    try:
        if check_db_connection():
            health_status["database"] = "connected"
        else:
            health_status["database"] = "disconnected"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Check AI service
    try:
        ai_client = get_ai_client()
        ai_health = await ai_client.health_check()
        health_status["ai_service"] = "connected"
        health_status["ai_models"] = ai_health.get("loaded_models", [])
    except Exception as e:
        health_status["ai_service"] = f"error: {str(e)}"
        if health_status["status"] == "healthy":
            health_status["status"] = "degraded"
    
    return health_status


# Include API routers
app.include_router(
    chats.router,
    prefix="/api/v1/chats",
    tags=["chats"]
)

app.include_router(
    models.router,
    prefix="/api/v1/models",
    tags=["models"]
)


# Legacy endpoints for backward compatibility
@app.get("/healthz")
async def legacy_health_check():
    """Legacy health check endpoint for backward compatibility"""
    health = await health_check()
    return {
        "status": "healthy" if health["status"] in ["healthy", "degraded"] else "unhealthy",
        "model_loaded": len(health.get("ai_models", [])) > 0,
        "active_sessions": 0  # This would need session tracking
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Fullstack Chat API v2.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("DEBUG", "false").lower() == "true"
    )
