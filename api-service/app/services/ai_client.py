import httpx
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID

logger = logging.getLogger(__name__)


class AIServiceClient:
    """Client for communicating with the AI service"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to AI service"""
        url = f"{self.base_url}{endpoint}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.request(method, url, **kwargs)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"AI service request failed: {e}")
                raise AIServiceError(f"AI service request failed: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error in AI service request: {e}")
                raise AIServiceError(f"Unexpected error: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check AI service health"""
        return await self._make_request("GET", "/health")
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models"""
        response = await self._make_request("GET", "/models")
        return response.get("models", [])
    
    async def get_model_status(self, model_id: str) -> Dict[str, Any]:
        """Get status of a specific model"""
        return await self._make_request("GET", f"/models/{model_id}/status")
    
    async def load_model(self, model_id: str) -> Dict[str, Any]:
        """Load a model"""
        return await self._make_request("POST", f"/models/{model_id}/load")
    
    async def unload_model(self, model_id: str) -> Dict[str, Any]:
        """Unload a model"""
        return await self._make_request("DELETE", f"/models/{model_id}/unload")
    
    async def generate_response(
        self,
        model_id: str,
        messages: List[Dict[str, str]],
        parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate AI response"""
        payload = {
            "model": model_id,
            "messages": messages,
            "parameters": parameters or {}
        }
        
        response = await self._make_request("POST", "/generate", json=payload)
        return response.get("response", "")
    
    async def chat_completion(
        self,
        model_id: str,
        messages: List[Dict[str, str]],
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Complete chat conversation"""
        payload = {
            "model": model_id,
            "messages": messages,
            "parameters": parameters or {}
        }
        
        return await self._make_request("POST", "/chat", json=payload)


class AIServiceError(Exception):
    """Custom exception for AI service errors"""
    pass


# Global AI client instance
_ai_client: Optional[AIServiceClient] = None


def get_ai_client() -> AIServiceClient:
    """Get AI service client instance"""
    global _ai_client
    if _ai_client is None:
        import os
        ai_service_url = os.getenv("AI_SERVICE_URL", "http://localhost:8001")
        _ai_client = AIServiceClient(ai_service_url)
    return _ai_client
