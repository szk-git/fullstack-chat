import os
import torch
import logging
from typing import Dict, Any, Optional, List
from transformers import (
    AutoTokenizer, AutoModelForCausalLM,
    BlenderbotTokenizer, BlenderbotForConditionalGeneration,
    pipeline
)
import gc

logger = logging.getLogger(__name__)

class ModelLoader:
    """Manages loading and unloading of Hugging Face models"""
    
    def __init__(self):
        self.loaded_models: Dict[str, Dict[str, Any]] = {}
        self.current_model: Optional[str] = None
        self.cache_dir = os.getenv('TRANSFORMERS_CACHE', '/app/.cache')
        
        # Define available models from environment or defaults
        default_models = os.getenv("DEFAULT_MODELS", "facebook/blenderbot-400M-distill,microsoft/DialoGPT-small")
        self.available_models = [model.strip() for model in default_models.split(",") if model.strip()]
        
        logger.info(f"ModelLoader initialized with cache dir: {self.cache_dir}")
        logger.info(f"Available models: {self.available_models}")
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models with their status"""
        models = []
        
        # Add the configured models
        for model_name in self.available_models:
            model_info = {
                "id": model_name,
                "name": self._get_friendly_name(model_name),
                "type": self._get_model_type(model_name),
                "is_loaded": model_name in self.loaded_models,
                "memory_usage": self._get_memory_usage(model_name)
            }
            models.append(model_info)
        
        return models
    
    def _get_friendly_name(self, model_name: str) -> str:
        """Convert model name to friendly display name"""
        name_map = {
            "facebook/blenderbot-400M-distill": "BlenderBot 400M",
            "microsoft/DialoGPT-small": "DialoGPT Small",
            "facebook/blenderbot-1B-distill": "BlenderBot 1B",
            "microsoft/DialoGPT-medium": "DialoGPT Medium",
            "microsoft/DialoGPT-large": "DialoGPT Large"
        }
        return name_map.get(model_name, model_name.split("/")[-1].replace("-", " ").title())
    
    def _get_model_type(self, model_name: str) -> str:
        """Determine model type based on name"""
        if "blenderbot" in model_name.lower():
            return "conversational"
        elif "dialogpt" in model_name.lower():
            return "dialog"
        else:
            return "text-generation"
    
    def _get_memory_usage(self, model_name: str) -> str:
        """Estimate memory usage for model"""
        if model_name in self.loaded_models:
            # Try to get actual memory usage
            try:
                model_obj = self.loaded_models[model_name]["model"]
                params = sum(p.numel() for p in model_obj.parameters())
                # Rough estimation: 4 bytes per parameter for float32
                memory_mb = (params * 4) / (1024 * 1024)
                if memory_mb > 1024:
                    return f"{memory_mb / 1024:.1f} GB"
                else:
                    return f"{memory_mb:.0f} MB"
            except:
                pass
        
        # Default estimates based on known model sizes
        size_estimates = {
            "facebook/blenderbot-400M-distill": "~1.6 GB",
            "microsoft/DialoGPT-small": "~500 MB",
            "facebook/blenderbot-1B-distill": "~4 GB",
            "microsoft/DialoGPT-medium": "~1.5 GB",
            "microsoft/DialoGPT-large": "~6 GB"
        }
        return size_estimates.get(model_name, "~1 GB")
    
    async def load_model(self, model_name: str) -> bool:
        """Load a specific model"""
        if model_name in self.loaded_models:
            logger.info(f"Model {model_name} is already loaded")
            return True
        
        try:
            logger.info(f"Loading model: {model_name}")
            
            # Load model and tokenizer based on type
            if "blenderbot" in model_name.lower():
                model = BlenderbotForConditionalGeneration.from_pretrained(
                    model_name,
                    cache_dir=self.cache_dir,
                    torch_dtype=torch.float32,
                    low_cpu_mem_usage=True
                )
                tokenizer = BlenderbotTokenizer.from_pretrained(
                    model_name,
                    cache_dir=self.cache_dir
                )
                
            else:  # DialoGPT and other causal LMs
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    cache_dir=self.cache_dir,
                    torch_dtype=torch.float32,
                    low_cpu_mem_usage=True,
                    pad_token_id=50256  # Common GPT-2 pad token
                )
                tokenizer = AutoTokenizer.from_pretrained(
                    model_name,
                    cache_dir=self.cache_dir
                )
                
                # Set pad token if not present
                if tokenizer.pad_token is None:
                    tokenizer.pad_token = tokenizer.eos_token
            
            # Store loaded model
            self.loaded_models[model_name] = {
                "model": model,
                "tokenizer": tokenizer,
                "type": self._get_model_type(model_name)
            }
            
            # Set as current model if it's the first one loaded
            if self.current_model is None:
                self.current_model = model_name
            
            logger.info(f"✓ Model {model_name} loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            return False
    
    async def unload_model(self, model_name: str) -> bool:
        """Unload a specific model"""
        if model_name not in self.loaded_models:
            logger.warning(f"Model {model_name} is not loaded")
            return False
        
        try:
            # Remove model from memory
            del self.loaded_models[model_name]
            
            # Force garbage collection
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            # Update current model if necessary
            if self.current_model == model_name:
                if self.loaded_models:
                    self.current_model = list(self.loaded_models.keys())[0]
                else:
                    self.current_model = None
            
            logger.info(f"✓ Model {model_name} unloaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unload model {model_name}: {e}")
            return False
    
    def get_loaded_models(self) -> List[str]:
        """Get list of currently loaded model names"""
        return list(self.loaded_models.keys())
    
    def is_model_loaded(self, model_name: str) -> bool:
        """Check if a model is currently loaded"""
        return model_name in self.loaded_models
    
    def get_current_model(self) -> Optional[str]:
        """Get the currently active model"""
        return self.current_model
    
    def set_current_model(self, model_name: str) -> bool:
        """Set the current active model"""
        if model_name not in self.loaded_models:
            logger.error(f"Cannot set current model to {model_name}: model not loaded")
            return False
        
        self.current_model = model_name
        logger.info(f"Current model set to: {model_name}")
        return True
    
    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a loaded model"""
        if model_name not in self.loaded_models:
            return None
        
        return {
            "name": model_name,
            "type": self.loaded_models[model_name]["type"],
            "is_current": model_name == self.current_model,
            "memory_usage": self._get_memory_usage(model_name)
        }
    
    async def generate_response(
        self, 
        model_name: str, 
        messages: List[Dict[str, str]], 
        parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate response using specified model"""
        if model_name not in self.loaded_models:
            raise ValueError(f"Model {model_name} is not loaded")
        
        model_data = self.loaded_models[model_name]
        model = model_data["model"]
        tokenizer = model_data["tokenizer"]
        model_type = model_data["type"]
        
        # Extract generation parameters
        params = parameters or {}
        max_length = min(params.get("max_tokens", 150), 500)  # Cap at 500 tokens
        temperature = max(0.1, min(params.get("temperature", 0.8), 1.0))
        do_sample = temperature > 0.1
        
        try:
            if model_type == "conversational":
                return await self._generate_blenderbot_response(
                    model, tokenizer, messages, max_length, temperature, do_sample
                )
            else:
                return await self._generate_dialogpt_response(
                    model, tokenizer, messages, max_length, temperature, do_sample
                )
                
        except Exception as e:
            logger.error(f"Generation failed for {model_name}: {e}")
            raise
    
    async def _generate_blenderbot_response(
        self, model, tokenizer, messages, max_length, temperature, do_sample
    ) -> str:
        """Generate response using BlenderBot"""
        # Get the last user message for BlenderBot
        user_messages = [msg["content"] for msg in messages if msg["role"] == "user"]
        if not user_messages:
            return "Hello! How can I help you today?"
        
        input_text = user_messages[-1]
        
        # Tokenize input
        inputs = tokenizer(input_text, return_tensors="pt", truncation=True, max_length=128)
        
        # Generate response
        with torch.no_grad():
            output = model.generate(
                **inputs,
                max_length=max_length,
                temperature=temperature,
                do_sample=do_sample,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
                num_return_sequences=1
            )
        
        # Decode response
        response = tokenizer.decode(output[0], skip_special_tokens=True)
        
        # Clean up response (remove input echo for BlenderBot)
        if input_text in response:
            response = response.replace(input_text, "").strip()
        
        return response or "I'm here to help! Could you please rephrase your question?"
    
    async def _generate_dialogpt_response(
        self, model, tokenizer, messages, max_length, temperature, do_sample
    ) -> str:
        """Generate response using DialoGPT"""
        # Build conversation context for DialoGPT
        conversation = []
        for msg in messages[-5:]:  # Use last 5 messages for context
            if msg["role"] in ["user", "assistant"]:
                conversation.append(msg["content"])
        
        if not conversation:
            return "Hello! I'm ready to chat with you."
        
        # Join conversation with special tokens
        input_text = tokenizer.eos_token.join(conversation) + tokenizer.eos_token
        
        # Tokenize
        inputs = tokenizer(input_text, return_tensors="pt", truncation=True, max_length=512)
        
        # Generate
        with torch.no_grad():
            output = model.generate(
                **inputs,
                max_length=inputs["input_ids"].shape[1] + max_length,
                temperature=temperature,
                do_sample=do_sample,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
                num_return_sequences=1
            )
        
        # Decode only the new tokens (response)
        new_tokens = output[0][inputs["input_ids"].shape[1]:]
        response = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
        
        return response or "I'm here to chat! What would you like to talk about?"
