"""
VAD (Voice Activity Detection) Base Classes

Provides modern streaming VAD interface.
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import Enum, unique
from typing import Union

from core.audio.audio_frame import AudioFrame
from core.utils.aio import Chan, cancel_and_wait


@unique
class VADEventType(str, Enum):
    START_OF_SPEECH = "start_of_speech"
    INFERENCE_DONE = "inference_done"
    END_OF_SPEECH = "end_of_speech"


@dataclass
class VADEvent:
    """
    Represents an event detected by the Voice Activity Detector (VAD).
    """

    type: VADEventType
    """Type of the VAD event (e.g., start of speech, end of speech, inference done)."""

    samples_index: int
    """Index of the audio sample where the event occurred, relative to the inference sample rate."""

    timestamp: float
    """Timestamp (in seconds) when the event was fired."""

    speech_duration: float
    """Duration of the speech segment in seconds."""

    silence_duration: float
    """Duration of the silence segment in seconds."""

    frames: list[AudioFrame] = field(default_factory=list)
    """
    List of audio frames associated with the speech.

    - For `start_of_speech` events, this contains the audio chunks that triggered the detection.
    - For `inference_done` events, this contains the audio chunks that were processed.
    - For `end_of_speech` events, this contains the complete user speech.
    """

    probability: float = 0.0
    """Probability that speech is present (only for `INFERENCE_DONE` events)."""

    inference_duration: float = 0.0
    """Time taken to perform the inference, in seconds (only for `INFERENCE_DONE` events)."""

    speaking: bool = False
    """Indicates whether speech was detected in the frames."""

    raw_accumulated_silence: float = 0.0
    """Threshold used to detect silence."""

    raw_accumulated_speech: float = 0.0
    """Threshold used to detect speech."""


@dataclass
class VADCapabilities:
    update_interval: float


class VAD(ABC):
    """
    Base class for Voice Activity Detection (VAD) providers.
    
    This is a modern, async-first VAD interface inspired by LiveKit's design.
    Providers should inherit from this class and implement the required methods.
    """
    
    def __init__(self, *, capabilities: VADCapabilities) -> None:
        """
        Initialize VAD provider.
        
        Args:
            capabilities: VAD capabilities (update interval, etc.)
        """
        self._capabilities = capabilities
        self._label = f"{type(self).__module__}.{type(self).__name__}"
    
    @property
    def model(self) -> str:
        return "unknown"
    
    @property
    def provider(self) -> str:
        return "unknown"
    
    @property
    def capabilities(self) -> VADCapabilities:
        """Get VAD capabilities"""
        return self._capabilities


class VADStream(ABC):
    """
    Base class for streaming VAD (push audio frames incrementally).
    
    This class handles:
    1. Input audio frame channel (for incremental audio input)
    2. Output VAD event channel (for detection results)
    3. Flush/end_input semantics
    
    Providers should inherit from this class and implement _main_task().
    """
    
    class _FlushSentinel:
        """Sentinel to mark segment boundaries"""
        pass
    
    def __init__(self, vad: VAD) -> None:
        """
        Initialize VADStream.
        
        Args:
            vad: The VAD provider instance
        """
        self._vad = vad
        self._input_ch: Chan[Union[AudioFrame, VADStream._FlushSentinel]] = Chan()
        self._event_ch: Chan[VADEvent] = Chan()
        
        # TODO: If metrics monitoring is needed in the future, the event channel should be teed
        #       to allow multiple consumers (main stream and metrics monitor)
        #       Example: self._event_aiter, monitor_aiter = tee(self._event_ch, 2)
        self._event_aiter = self._event_ch
        self._task = asyncio.create_task(self._main_task(), name="VADStream._main_task")
        self._task.add_done_callback(lambda _: self._event_ch.close())
    
    @abstractmethod
    async def _main_task(self) -> None:
        """
        Provider-specific streaming VAD implementation.
        
        This method should:
        1. Read from self._input_ch and process audio frames
        2. Perform VAD inference on audio frames
        3. Push VADEvent objects to self._event_ch as detection results become available
        4. Handle flush signals and end_of_input
        
        The method should push VADEvent objects to self._event_ch as detection
        results become available.
        """
        ...
    
    def push_frame(self, frame: AudioFrame) -> None:
        """Push audio frame to be processed"""
        self._check_input_not_ended()
        self._check_not_closed()
        self._input_ch.send_nowait(frame)
    
    def flush(self) -> None:
        """Mark the end of the current segment"""
        self._check_input_not_ended()
        self._check_not_closed()
        self._input_ch.send_nowait(self._FlushSentinel())
    
    def end_input(self) -> None:
        """Mark the end of input, no more audio will be pushed"""
        self.flush()
        self._input_ch.close()
    
    async def aclose(self) -> None:
        """Close the stream immediately"""
        self._input_ch.close()
        await cancel_and_wait(self._task)
        self._event_ch.close()
    
    async def __anext__(self) -> VADEvent:
        try:
            val = await self._event_aiter.__anext__()
        except StopAsyncIteration:
            if not self._task.cancelled() and (exc := self._task.exception()):
                raise exc
            
            raise StopAsyncIteration from None
        
        return val
    
    def __aiter__(self) -> AsyncIterator[VADEvent]:
        return self
    
    def _check_not_closed(self) -> None:
        if self._event_ch.closed:
            cls = type(self)
            raise RuntimeError(f"{cls.__module__}.{cls.__name__} is closed")
    
    def _check_input_not_ended(self) -> None:
        if self._input_ch.closed:
            cls = type(self)
            raise RuntimeError(f"{cls.__module__}.{cls.__name__} input ended")


# Factory function for creating VAD instances from configuration

async def create_from_config(config) -> VAD:
    """
    Factory function to create VAD instance from configuration.
    
    This function dispatches to the appropriate VAD provider based on
    the configuration. Currently only supports Silero VAD.
    
    Args:
        config: VAD configuration object (from config.components.vad)
        
    Returns:
        Initialized VAD instance
        
    Raises:
        ValueError: If the specified provider is not supported
        RuntimeError: If VAD initialization fails
        
    Example:
        from config.models import Config
        config = load_config("config.yaml")
        vad = await create_from_config(config.components.vad)
    """

    
    provider = config.provider.lower()
    logging.info(f"Creating VAD: provider={provider}")
    
    if provider == "silero":
        from .silero import VAD as SileroVAD
        return await SileroVAD.from_config(config)
    else:
        raise ValueError(f"Unsupported VAD provider: {provider}")

