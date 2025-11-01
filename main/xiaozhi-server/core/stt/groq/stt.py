"""
Groq STT Implementation

Speech-to-Text using Groq's API.
Groq API is fully compatible with OpenAI's API, so this implementation
extends the OpenAI STT class with Groq-specific configuration.
"""

from __future__ import annotations

import os

import openai

from ..openai.stt import STT as OpenAISTT
from core.utils.types import NOT_GIVEN, NotGivenOr, is_given

from .models import STTModels



class STT(OpenAISTT):
    """
    Groq Speech-to-Text (STT) class.
    
    This class extends OpenAI's STT implementation since Groq's API
    is fully compatible with OpenAI's API. It only needs to configure
    the base URL and API key handling for Groq.
    
    Args:
        model: The Groq model to use for transcription.
              Options: "whisper-large-v3", "whisper-large-v3-turbo"
        language: The language code to use for transcription (e.g., "en" for English).
                 Use empty string "" for auto-detection.
        prompt: Optional text prompt to guide the transcription.
        api_key: Your Groq API key. If not provided, will use the GROQ_API_KEY environment variable.
        base_url: Custom base URL for Groq API. Defaults to "https://api.groq.com/openai/v1".
        client: Optional pre-configured OpenAI AsyncClient instance.
    """
    
    def __init__(
        self,
        *,
        model: STTModels | str = "whisper-large-v3-turbo",
        language: str = "en",
        prompt: NotGivenOr[str] = NOT_GIVEN,
        api_key: NotGivenOr[str] = NOT_GIVEN,
        base_url: str | None = None,
        client: openai.AsyncClient | None = None,
    ) -> None:
        """
        Create a new instance of Groq STT.
        
        ``api_key`` must be set to your Groq API key, either using the argument or by setting
        the ``GROQ_API_KEY`` environmental variable.
        """
        # Get API key from environment if not provided
        groq_api_key = api_key if is_given(api_key) else os.environ.get("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError(
                "GROQ_API_KEY is required, either as argument or set GROQ_API_KEY environmental variable"
            )
        
        # Set default base URL for Groq
        if base_url is None:
            base_url = "https://api.groq.com/openai/v1"
        
        # Call parent constructor with Groq-specific configuration
        super().__init__(
            model=model,
            language=language,
            prompt=prompt if is_given(prompt) else None,
            api_key=groq_api_key,
            base_url=base_url,
            client=client,
        )
    
    @classmethod
    async def from_config(cls, config) -> STT:
        """
        Create Groq STT instance from configuration.
        
        Args:
            config: STT configuration object with structure:
                - provider: "groq"
                - model:
                    - name: model name (e.g., "whisper-large-v3")
                    - base_url: optional custom base URL
                - options: optional dict with language, prompt, etc.
        
        Returns:
            Initialized Groq STT instance
        """
        options = config.options or {}
        
        instance = cls(
            model=config.model.name,
            language=options.get("language", "en"),
            prompt=options.get("prompt", NOT_GIVEN),
            base_url=config.model.base_url if config.model.base_url else None,
            api_key=options.get("api_key", NOT_GIVEN),  # Will read from env
        )
        
        return instance

