#!/usr/bin/env python3
"""
Pre-load models during Docker build to avoid runtime download issues
"""
import os
import sys
from transformers import (
    AutoTokenizer, AutoModelForCausalLM,
    BlenderbotTokenizer, BlenderbotForConditionalGeneration,
    GPT2LMHeadModel, GPT2Tokenizer
)

# Set cache directories
os.environ['TRANSFORMERS_CACHE'] = '/app/.cache'
os.environ['HF_HOME'] = '/app/.cache'
os.environ['HF_HUB_CACHE'] = '/app/.cache/hub'

def preload_model(model_name, model_type="auto"):
    """Preload a single model with error handling"""
    try:
        print(f"Pre-loading {model_name}...")
        
        # Handle specific models based on name patterns
        if "blenderbot" in model_name.lower():
            print(f"Loading BlenderBot model: {model_name}")
            model = BlenderbotForConditionalGeneration.from_pretrained(
                model_name, 
                cache_dir='/app/.cache',
                torch_dtype="float32",
                low_cpu_mem_usage=True
            )
            tokenizer = BlenderbotTokenizer.from_pretrained(model_name, cache_dir='/app/.cache')
            
        elif "dialogpt" in model_name.lower() or "gpt2" in model_name.lower():
            print(f"Loading GPT-2/DialoGPT model: {model_name}")
            model = AutoModelForCausalLM.from_pretrained(
                model_name, 
                cache_dir='/app/.cache',
                torch_dtype="float32",
                low_cpu_mem_usage=True
            )
            tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir='/app/.cache')
            
        else:
            print(f"Loading generic model: {model_name}")
            # Try AutoModel first, fallback to AutoModelForCausalLM
            try:
                model = AutoModelForCausalLM.from_pretrained(
                    model_name, 
                    cache_dir='/app/.cache',
                    torch_dtype="float32",
                    low_cpu_mem_usage=True
                )
            except:
                from transformers import AutoModel
                model = AutoModel.from_pretrained(
                    model_name, 
                    cache_dir='/app/.cache',
                    torch_dtype="float32",
                    low_cpu_mem_usage=True
                )
            tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir='/app/.cache')
        
        # Handle tokenizer padding
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            
        print(f"✓ {model_name} loaded successfully")
        del model, tokenizer
        return True
        
    except Exception as e:
        print(f"✗ Failed to pre-load {model_name}: {e}")
        import traceback
        traceback.print_exc()
        return False

def preload_models():
    print("Starting model pre-loading...")
    
    # Get models from environment variable
    default_models = os.getenv("DEFAULT_MODELS", "facebook/blenderbot-400M-distill,microsoft/DialoGPT-small").split(",")
    
    loaded_count = 0
    for model_name in default_models:
        model_name = model_name.strip()
        if model_name:
            if preload_model(model_name):
                loaded_count += 1
    
    print(f"Model pre-loading completed: {loaded_count}/{len(default_models)} models loaded")

if __name__ == "__main__":
    preload_models()
