"""
OpenAI STT Implementation

Speech-to-Text using OpenAI's transcription API.
Supports non-streaming recognition via Whisper and other OpenAI models.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx
import openai
from openai.types.audio import TranscriptionVerbose
import logging

from core.audio.audio_frame import AudioFrame
from ..base import (
    STT,
    STTCapabilities,
    AudioBuffer,
    SpeechData,
    SpeechEvent,
    SpeechEventType,
)
from .. import base
from core.utils.errors import APIConnectionError, APITimeoutError, APIStatusError
from core.utils.types import APIConnectOptions, NOT_GIVEN, NotGivenOr, is_given
from core.utils.short_uuid import shortuuid

from .models import STTModels


@dataclass
class _STTOptions:
    model: STTModels | str
    language: str
    prompt: NotGivenOr[str]


class STT(base.STT):
    """
    OpenAI Speech-to-Text (STT) class.
    
    This class provides functionality to transcribe audio data using OpenAI's
    transcription API (Whisper and other models).
    """
    
    def __init__(
        self,
        *,
        model: STTModels | str = "whisper-1",
        language: str = "en",
        prompt: NotGivenOr[str] = NOT_GIVEN,
        api_key: NotGivenOr[str] = NOT_GIVEN,
        base_url: NotGivenOr[str] = NOT_GIVEN,
        client: openai.AsyncClient | None = None,
    ) -> None:
        """
        Create a new instance of OpenAI STT.
        
        Args:
            model: The OpenAI model to use for transcription.
                  Options: "whisper-1", "gpt-4o-mini-transcribe", "gpt-4o-transcribe"
            language: The language code to use for transcription (e.g., "en" for English).
                     Use empty string "" for auto-detection.
            prompt: Optional text prompt to guide the transcription. Only supported for whisper-1.
            api_key: Your OpenAI API key. If not provided, will use the OPENAI_API_KEY environment variable.
            base_url: Custom base URL for OpenAI API.
            client: Optional pre-configured OpenAI AsyncClient instance.
        """
        super().__init__(
            capabilities=STTCapabilities(
                streaming=False,  # Non-streaming only for now
                interim_results=False,
            )
        )
        
        self._opts = _STTOptions(
            model=model,
            language=language,
            prompt=prompt,
        )
        
        self._client = client or openai.AsyncClient(
            max_retries=0,  # We handle retries ourselves
            api_key=api_key if is_given(api_key) else None,
            base_url=base_url if is_given(base_url) else None,
            http_client=httpx.AsyncClient(
                timeout=httpx.Timeout(connect=15.0, read=30.0, write=5.0, pool=5.0),
                follow_redirects=True,
                limits=httpx.Limits(
                    max_connections=50,
                    max_keepalive_connections=50,
                    keepalive_expiry=120,
                ),
            ),
        )
    
    @classmethod
    async def from_config(cls, config) -> STT:
        """
        Create OpenAI STT instance from configuration.
        
        Args:
            config: STT configuration object
        
        Returns:
            Initialized OpenAI STT instance
        """
        options = config.options or {}
        
        instance = cls(
            model=config.model.name,
            language=options.get("language", "en"),
            prompt=options.get("prompt", NOT_GIVEN),
            base_url=config.model.base_url if config.model.base_url else NOT_GIVEN,
            api_key=NOT_GIVEN,  # Will read from env
        )
        
        return instance
    
    @property
    def model(self) -> str:
        """Get the model name"""
        return self._opts.model
    
    @property
    def provider(self) -> str:
        """Get the provider name"""
        base_url = self._client.base_url
        if base_url:
            # Extract hostname from URL
            if hasattr(base_url, "netloc"):
                netloc = base_url.netloc.decode("utf-8") if isinstance(base_url.netloc, bytes) else base_url.netloc
                return netloc
            else:
                # Fallback: try to extract from string representation
                url_str = str(base_url)
                if "://" in url_str:
                    return url_str.split("://")[1].split("/")[0]
                return url_str
        return "openai.com"
    
    async def _recognize_impl(
        self,
        buffer: AudioBuffer,
        *,
        language: NotGivenOr[str] = NOT_GIVEN,
        conn_options: APIConnectOptions,
    ) -> SpeechEvent:
        """
        Provider-specific recognition implementation.
        
        Args:
            buffer: Audio buffer (list of AudioFrame or single AudioFrame)
            language: Optional language code for recognition (overrides instance language)
            conn_options: Connection options for API calls
        
        Returns:
            SpeechEvent: Recognition result with transcript and metadata
        """
        try:
            # Use provided language or fall back to instance language
            recognition_language = (
                language if is_given(language) else self._opts.language
            )
            
            # Combine audio frames into a single frame
            if isinstance(buffer, list):
                if not buffer:
                    raise ValueError("Empty audio buffer provided")
                combined_frame = AudioFrame.combine_frames(buffer)
            else:
                combined_frame = buffer
            
            # Convert to WAV format bytes
            wav_data = combined_frame.to_wav_bytes()
            
            # Prepare prompt (only supported for whisper-1)
            prompt = self._opts.prompt if is_given(self._opts.prompt) else openai.NOT_GIVEN
            
            # Determine response format
            # verbose_json returns language and other details, only supported for whisper-1
            response_format = "json"
            if self._opts.model == "whisper-1":
                response_format = "verbose_json"
            
            # Call OpenAI API
            resp = await self._client.audio.transcriptions.create(
                file=(
                    "file.wav",
                    wav_data,
                    "audio/wav",
                ),
                model=self._opts.model,  # type: ignore
                language=recognition_language if recognition_language else None,
                prompt=prompt,
                response_format=response_format,
                timeout=httpx.Timeout(
                    connect=conn_options.timeout,
                    read=conn_options.timeout * 2,  # Allow more time for read
                ),
            )
            
            # Extract language from response if available
            detected_language = recognition_language
            if isinstance(resp, TranscriptionVerbose) and resp.language:
                detected_language = resp.language
            
            # Create SpeechData
            speech_data = SpeechData(
                text=resp.text,
                language=detected_language,
            )
            
            # Create SpeechEvent
            request_id = shortuuid("asr_openai_")
            return SpeechEvent(
                type=SpeechEventType.FINAL_TRANSCRIPT,
                request_id=request_id,
                alternatives=[speech_data],
            )
        
        except openai.APITimeoutError as e:
            raise APITimeoutError(
                f"OpenAI STT request timed out: {e}",
                timeout=conn_options.timeout,
            ) from None
        
        except openai.APIStatusError as e:
            status_code = e.status_code if hasattr(e, "status_code") else None
            
            # Handle specific error types
            if status_code == 401:
                raise APIStatusError(
                    "Invalid OpenAI API key",
                    status_code=status_code,
                    response_body=str(e),
                ) from None
            elif status_code == 429:
                raise APIStatusError(
                    "OpenAI API rate limit exceeded",
                    status_code=status_code,
                    response_body=str(e),
                ) from None
            
            raise APIStatusError(
                f"OpenAI STT API error: {e}",
                status_code=status_code,
                response_body=str(e),
            ) from None
        
        except Exception as e:
            logging.error(
                f"OpenAI STT recognition failed: {e}",
                exc_info=e,
            )
            raise APIConnectionError(
                f"Failed to recognize speech with OpenAI: {e}"
            ) from e

