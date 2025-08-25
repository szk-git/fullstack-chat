from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager

from .services.generation_service import GenerationService
from .services.model_loader import ModelLoader
from .schemas.ai_schemas import GenerateRequest, GenerateResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
model_loader = ModelLoader()
generation_service = GenerationService(model_loader)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage AI service lifecycle"""
    logger.info("Starting AI Service...")
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down AI Service...")


app = FastAPI(
    title="AI Inference Service",
    version="1.0.0",
    description="Dedicated service for AI model inference and management",
    lifespan=lifespan
)

# Configure CORS for internal service communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "AI Inference Service"}


@app.post("/generate", response_model=GenerateResponse)
async def generate_response(request: GenerateRequest):
    """Generate AI response"""
    try:
        logger.debug(f"Generation request received - Messages: {len(request.messages)}, Parameters: {request.parameters}")
        
        # Use the first available model if no current model set
        if not hasattr(model_loader, 'current_model') or model_loader.current_model is None:
            available = model_loader.get_available_models()
            if available:
                model_loader.current_model = available[0]['id']
        
        target_model = request.model or model_loader.get_current_model()
        logger.debug(f"Using model: {target_model}")
        
        # Log chat settings from parameters and system messages
        chat_settings = request.parameters or {}
        
        # Count system messages in the messages array
        system_messages = [msg for msg in request.messages if msg.role == 'system']
        system_prompt_length = sum(len(msg.content) for msg in system_messages)
        
        if any(key in chat_settings for key in ['temperature', 'max_tokens']) or system_messages:
            settings_summary = {
                'temperature': chat_settings.get('temperature', 'default'),
                'max_tokens': chat_settings.get('max_tokens', 'default'),
                'system_prompt_length': system_prompt_length
            }
            logger.debug(f"Chat settings applied - Model: {target_model}: {settings_summary}")
        
        # Generate response using the generation service
        response_text = await generation_service.generate_response(
            model_id=target_model,
            messages=request.messages,
            parameters=chat_settings
        )
        
        return GenerateResponse(
            response=response_text,
            model=target_model,
            usage={
                "prompt_tokens": len(str(request.messages)),
                "completion_tokens": len(response_text),
                "total_tokens": len(str(request.messages)) + len(response_text)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@app.post("/chat", response_model=GenerateResponse)
async def chat_completion(request: GenerateRequest):
    """Chat completion endpoint (alias for generate)"""
    return await generate_response(request)


# Real Model Management Endpoints using Hugging Face models

@app.get("/models")
async def list_models():
    """List all available AI models"""
    try:
        models = model_loader.get_available_models()
        return {"models": models}
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")


@app.get("/models/{model_id:path}/status")
async def get_model_status(model_id: str):
    """Get status of a specific model"""
    try:
        available_models = model_loader.get_available_models()
        model = next((m for m in available_models if m["id"] == model_id), None)
        if not model:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
        
        return {
            "model_id": model_id,
            "status": "loaded" if model["is_loaded"] else "available",
            "memory_usage": model["memory_usage"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get model status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get model status: {str(e)}")


@app.post("/models/{model_id:path}/load")
async def load_model_endpoint(model_id: str):
    """Load a specific model"""
    try:
        available_models = model_loader.get_available_models()
        model = next((m for m in available_models if m["id"] == model_id), None)
        if not model:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
        
        # Actually load the model using model_loader
        success = await model_loader.load_model(model_id)
        if not success:
            raise HTTPException(status_code=500, detail=f"Failed to load model {model_id}")
        
        return {
            "status": "loaded",
            "model_id": model_id,
            "message": f"Model {model_id} loaded successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load model {model_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")


@app.delete("/models/{model_id:path}/unload")
async def unload_model_endpoint(model_id: str):
    """Unload a specific model"""
    try:
        if not model_loader.is_model_loaded(model_id):
            raise HTTPException(status_code=404, detail=f"Model {model_id} is not loaded")
        
        # Actually unload the model using model_loader
        success = await model_loader.unload_model(model_id)
        if not success:
            raise HTTPException(status_code=500, detail=f"Failed to unload model {model_id}")
        
        return {
            "status": "unloaded",
            "model_id": model_id,
            "message": f"Model {model_id} unloaded successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unload model {model_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to unload model: {str(e)}")


@app.post("/models/{model_id:path}/switch")
async def switch_model(model_id: str):
    """Switch to a specific model"""
    try:
        available_models = model_loader.get_available_models()
        model = next((m for m in available_models if m["id"] == model_id), None)
        if not model:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
        
        # Load the model if not already loaded
        if not model_loader.is_model_loaded(model_id):
            success = await model_loader.load_model(model_id)
            if not success:
                raise HTTPException(status_code=500, detail=f"Failed to load model {model_id}")
        
        # Set as current model
        success = model_loader.set_current_model(model_id)
        if not success:
            raise HTTPException(status_code=500, detail=f"Failed to set current model to {model_id}")
        
        logger.info(f"Switched to model: {model_id}")
        
        return {
            "status": "success",
            "current_model": model_id,
            "message": f"Switched to {model['name']}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to switch to model {model_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to switch model: {str(e)}")


@app.get("/models/current")
async def get_current_model():
    """Get the currently active model"""
    try:
        current = model_loader.get_current_model()
        return {"current_model": current}
    except Exception as e:
        logger.error(f"Failed to get current model: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get current model: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
