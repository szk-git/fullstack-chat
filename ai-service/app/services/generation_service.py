import logging
from typing import List, Dict, Any
from ..schemas.ai_schemas import Message
from .model_loader import ModelLoader

logger = logging.getLogger(__name__)


class GenerationService:
    """Handles AI text generation using loaded models"""
    
    def __init__(self, model_loader: ModelLoader):
        self.model_loader = model_loader
    
    async def generate_response(
        self, 
        model_id: str, 
        messages: List[Message], 
        parameters: Dict[str, Any] = None
    ) -> str:
        """Generate response using the specified model"""
        
        logger.debug(f"Starting generation - Model: {model_id}")
        logger.debug(f"Message count: {len(messages)}")
        logger.debug(f"Input parameters: {parameters}")
        
        try:
            # Check if model is loaded
            if not self.model_loader.is_model_loaded(model_id):
                # Try to load the model first
                logger.info(f"Model {model_id} not loaded, attempting to load...")
                success = await self.model_loader.load_model(model_id)
                if not success:
                    # Fallback to a mock response if model loading fails
                    logger.warning(f"Failed to load model {model_id}, falling back to mock response")
                    return self._generate_fallback_response(model_id, messages)
            
            # Convert Message objects to dictionaries for model_loader
            message_dicts = [
                {"role": msg.role, "content": msg.content} 
                for msg in messages
            ]
            
            # Use the real model to generate response
            response = await self.model_loader.generate_response(
                model_name=model_id,
                messages=message_dicts,
                parameters=parameters
            )
            
            logger.debug(f"Generation completed - Model: {model_id}, Response length: {len(response)} chars")
            return response
            
        except Exception as e:
            logger.error(f"Generation failed for model {model_id}: {e}")
            # Return fallback response instead of raising exception
            return self._generate_fallback_response(model_id, messages)
    
    def _generate_fallback_response(self, model_id: str, messages: List[Message]) -> str:
        """Generate fallback response when model fails"""
        user_messages = [msg for msg in messages if msg.role == "user"]
        if not user_messages:
            return f"Hello! I'm {self._get_model_display_name(model_id)}. How can I help you today?"
        
        latest_message = user_messages[-1].content
        return f"I understand you're asking about '{latest_message}'. I'm {self._get_model_display_name(model_id)}, and I'm here to help, though I'm currently running in a limited mode."
    
    def _get_model_display_name(self, model_id: str) -> str:
        """Get friendly display name for model"""
        name_map = {
            "facebook/blenderbot-400M-distill": "BlenderBot",
            "microsoft/DialoGPT-small": "DialoGPT",
        }
        return name_map.get(model_id, model_id.split("/")[-1])
    
    def _get_greeting_response(self, model_id: str) -> str:
        """Generate model-appropriate greeting"""
        greetings = {
            "gpt-3.5-turbo": "Hello! I'm ChatGPT, powered by GPT-3.5. How can I assist you today?",
            "gpt-4": "Hello! I'm ChatGPT, powered by GPT-4. I'm here to help with any questions or tasks you have.",
            "claude-instant": "Hello! I'm Claude, an AI assistant created by Anthropic. How can I help you today?",
            "llama-2-7b": "Hello! I'm LLaMA 2, a conversational AI model. What would you like to discuss?"
        }
        return greetings.get(model_id, "Hello! How can I help you today?")
    
    def _generate_contextual_response(self, model_id: str, user_message: str, messages: List[Message], parameters: Dict[str, Any] = None) -> str:
        """Generate contextual response based on model and message content"""
        # Analyze message content for context
        message_lower = user_message.lower()
        
        # Get conversation context
        conversation_length = len([msg for msg in messages if msg.role in ["user", "assistant"]])
        has_system_prompt = any(msg.role == "system" for msg in messages)
        
        # Model-specific response patterns
        if model_id == "gpt-4":
            return self._generate_gpt4_response(user_message, message_lower, conversation_length, has_system_prompt)
        elif model_id == "gpt-3.5-turbo":
            return self._generate_gpt35_response(user_message, message_lower, conversation_length, has_system_prompt)
        elif model_id == "claude-instant":
            return self._generate_claude_response(user_message, message_lower, conversation_length, has_system_prompt)
        elif model_id == "llama-2-7b":
            return self._generate_llama_response(user_message, message_lower, conversation_length, has_system_prompt)
        else:
            return self._generate_default_response(user_message, message_lower, conversation_length, has_system_prompt)
    
    def _generate_gpt4_response(self, user_message: str, message_lower: str, conversation_length: int, has_system_prompt: bool) -> str:
        """Generate GPT-4 style response"""
        if "hello" in message_lower or "hi" in message_lower:
            return "Hello! I'm GPT-4, ready to help with complex reasoning, analysis, and creative tasks. What would you like to explore today?"
        elif any(word in message_lower for word in ["help", "what can you do", "capabilities"]):
            return "I'm GPT-4, and I can help with a wide range of tasks including complex analysis, creative writing, coding, math problem solving, research assistance, and nuanced conversations. I'm designed to provide detailed, accurate, and thoughtful responses. What specific area interests you?"
        elif any(word in message_lower for word in ["code", "programming", "python", "javascript"]):
            return "I'd be happy to help with programming! I can assist with code writing, debugging, explaining concepts, reviewing code, and solving algorithmic problems across many programming languages. What coding challenge are you working on?"
        elif any(word in message_lower for word in ["explain", "how", "why", "what is"]):
            return f"I'd be glad to explain that for you. Let me break down '{user_message}' in a clear and comprehensive way. Could you specify which aspect you'd like me to focus on, or would you like a general overview?"
        else:
            return f"That's an interesting point about '{user_message}'. As GPT-4, I can provide a detailed analysis of this topic. Let me consider the various aspects and implications involved..."
    
    def _generate_gpt35_response(self, user_message: str, message_lower: str, conversation_length: int, has_system_prompt: bool) -> str:
        """Generate GPT-3.5 Turbo style response"""
        if "hello" in message_lower or "hi" in message_lower:
            return "Hi there! I'm ChatGPT powered by GPT-3.5 Turbo. I'm here to help with your questions and tasks. How can I assist you?"
        elif any(word in message_lower for word in ["help", "what can you do"]):
            return "I'm GPT-3.5 Turbo and I can help with many things: answering questions, writing, coding, analysis, math, creative tasks, and more. What would you like help with?"
        elif any(word in message_lower for word in ["thank", "thanks"]):
            return "You're welcome! I'm happy to help. Is there anything else you'd like to know or discuss?"
        else:
            return f"Regarding '{user_message}', I can help you with that. Let me provide you with a helpful response based on what you've asked."
    
    def _generate_claude_response(self, user_message: str, message_lower: str, conversation_length: int, has_system_prompt: bool) -> str:
        """Generate Claude style response"""
        if "hello" in message_lower or "hi" in message_lower:
            return "Hello! I'm Claude, an AI assistant made by Anthropic. I'm here to help with a wide variety of tasks. What can I assist you with today?"
        elif any(word in message_lower for word in ["help", "what can you do"]):
            return "I'm Claude, and I aim to be helpful, harmless, and honest. I can assist with analysis, writing, math, coding, creative projects, answering questions, and having thoughtful conversations. How can I help you today?"
        elif any(word in message_lower for word in ["thank", "thanks"]):
            return "You're very welcome! I'm glad I could be helpful. Please feel free to ask if you have any other questions."
        else:
            return f"I'd be happy to help you with '{user_message}'. Let me think about this carefully and provide you with a thoughtful response."
    
    def _generate_llama_response(self, user_message: str, message_lower: str, conversation_length: int, has_system_prompt: bool) -> str:
        """Generate LLaMA style response"""
        if "hello" in message_lower or "hi" in message_lower:
            return "Hello! I'm LLaMA 2, a large language model trained by Meta. I'm designed to be helpful and provide informative responses. What would you like to talk about?"
        elif any(word in message_lower for word in ["help", "what can you do"]):
            return "I'm LLaMA 2, and I can help with various tasks like answering questions, explaining concepts, helping with writing, and engaging in conversations. I aim to be helpful while being factual and balanced. What interests you?"
        else:
            return f"Regarding your message about '{user_message}', I'll do my best to provide you with a helpful and informative response."
    
    def _generate_default_response(self, user_message: str, message_lower: str, conversation_length: int, has_system_prompt: bool) -> str:
        """Generate default response for unknown models"""
        if "hello" in message_lower or "hi" in message_lower:
            return "Hello! I'm an AI assistant. How can I help you today?"
        elif any(word in message_lower for word in ["help", "what can you do"]):
            return "I'm an AI assistant that can help with questions, provide information, assist with writing, and engage in conversations. What would you like help with?"
        else:
            return f"I understand you're asking about '{user_message}'. I'll do my best to provide a helpful response."
    
