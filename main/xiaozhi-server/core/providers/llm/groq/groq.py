from core.providers.llm.openai.openai import LLMProvider as OpenAILLMProvider
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()


class LLMProvider(OpenAILLMProvider):
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
        
        logger.bind(tag=TAG).info(
            f"Groq LLM Provider initialized: model={self.model_name}, "
            f"base_url={self.base_url}"
        )

