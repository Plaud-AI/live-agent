"""
Groq LLM Provider
"""
from __future__ import annotations
import core.llm.openai as OpenAI
import logging


class LLM(OpenAI.LLM):
    """
    Groq LLM Provider - Compatible with OpenAI API
    
    Groq provides high-performance LLM inference using custom hardware.
    Supports models you can find in the console.groq.com
    
    API Documentation: https://console.groq.com/docs/quickstart
    """
    
    def __init__(self, config):
        # Set default Groq base_url if not provided
        if "base_url" not in config and "url" not in config:
            config["base_url"] = "https://api.groq.com/openai/v1"
        
        # Set default model if not provided
        if "model_name" not in config:
            config["model_name"] = "openai/gpt-oss-120b"
        
        # Groq has specific timeout requirements
        # Default to 60 seconds for Groq (faster inference)
        if "timeout" not in config:
            config["timeout"] = 60
        
        # Call parent constructor
        super().__init__(config)
        
        logging.info(
            f"Groq LLM Provider initialized: model={self.model_name}, "
            f"base_url={self.base_url}"
        )
    
    @classmethod
    async def from_config(cls, config) -> LLM:
        """
        Create Groq LLM instance from configuration.
        
        Args:
            config: LLM configuration object with structure:
                - provider: "groq"
                - model:
                    - name: model name (e.g., "openai/gpt-oss-120b")
                    - base_url: optional custom base URL
                - options: optional dict with:
                    - api_key: API key (or from env GROQ_API_KEY)
                    - timeout: request timeout in seconds (default: 60)
                    - max_retries: maximum retry attempts
                    - max_output_tokens: maximum output tokens
                    - temperature: sampling temperature
                    - top_p: nucleus sampling parameter
                    - frequency_penalty: frequency penalty
        
        Returns:
            Initialized Groq LLM instance
        """
        import os
        
        options = config.options or {}
        
        # Build config dict for __init__
        llm_config = {
            "model_name": config.model.name,
            "base_url": config.model.base_url if config.model.base_url else "https://api.groq.com/openai/v1",
            "api_key": options.get("api_key") or os.environ.get("GROQ_API_KEY"),
            "timeout": options.get("timeout", 60),  # Groq-specific: faster default
            "max_retries": options.get("max_retries", 0),
            "max_output_tokens": options.get("max_output_tokens", 500),
            "temperature": options.get("temperature", 0.7),
            "top_p": options.get("top_p", 1.0),
            "frequency_penalty": options.get("frequency_penalty", 0),
        }
        
        instance = cls(llm_config)
        
        logging.info(
            f"✓ Groq LLM loaded: model={config.model.name}, "
            f"base_url={llm_config['base_url']}"
        )
        
        return instance

