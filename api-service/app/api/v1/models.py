from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from ...services.ai_client import get_ai_client, AIServiceError

router = APIRouter()


@router.get("/")
async def list_models() -> List[Dict[str, Any]]:
    """List all available AI models"""
    try:
        ai_client = get_ai_client()
        models = await ai_client.list_models()
        return models
        
    except AIServiceError as e:
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")


@router.get("/{model_id}/status")
async def get_model_status(model_id: str) -> Dict[str, Any]:
    """Get status of a specific model"""
    try:
        ai_client = get_ai_client()
        status = await ai_client.get_model_status(model_id)
        return status
        
    except AIServiceError as e:
        if "404" in str(e):
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model status: {str(e)}")


@router.post("/{model_id}/load")
async def load_model(model_id: str) -> Dict[str, Any]:
    """Load a specific model"""
    try:
        ai_client = get_ai_client()
        result = await ai_client.load_model(model_id)
        return result
        
    except AIServiceError as e:
        if "404" in str(e):
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")


@router.delete("/{model_id}/unload")
async def unload_model(model_id: str) -> Dict[str, Any]:
    """Unload a specific model"""
    try:
        ai_client = get_ai_client()
        result = await ai_client.unload_model(model_id)
        return result
        
    except AIServiceError as e:
        if "404" in str(e):
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to unload model: {str(e)}")


@router.get("/health")
async def check_ai_service_health() -> Dict[str, Any]:
    """Check AI service health"""
    try:
        ai_client = get_ai_client()
        health = await ai_client.health_check()
        return health
        
    except AIServiceError as e:
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check AI service health: {str(e)}")
