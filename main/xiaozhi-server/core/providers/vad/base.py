from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterable, AsyncIterator
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field
from core.utils.channel import Chan
from core.utils.task import cancel_and_wait
from core.utils.audio import AudioFrame


class VADEventType(str, Enum):
    """VAD event types"""
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
    
    timestamp: float
    """Timestamp (in seconds) when the event was fired."""

    speech_duration: float
    """Duration of the speech segment in seconds."""

    silence_duration: float
    """Duration of the silence segment in seconds."""

    frames: list[AudioFrame] = field(default_factory=list)
    """
    List of AudioFrame objects associated with the speech.

    - For `start_of_speech` events, this contains the audio frames that triggered the detection.
    - For `inference_done` events, this contains the audio frames that were processed.
    - For `end_of_speech` events, this contains the complete user speech as AudioFrame objects.
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
    
    def __init__(self, *, capabilities: VADCapabilities) -> None:
        super().__init__()
        self._capabilities = capabilities

    
    @property
    def model(self) -> str:
        return "unknown"

    @property
    def provider(self) -> str:
        return "unknown"

    @property
    def capabilities(self) -> VADCapabilities:
        return self._capabilities

    @abstractmethod
    def stream(self) -> VADStream: ...

class VADStream(ABC):
    class _FlushSentinel:
        pass

    def __init__(self, vad: VAD) -> None:
        self._vad = vad
        self._input_ch = Chan[AudioFrame]()
        self._event_ch = Chan[VADEvent]()

        self._event_aiter = self._event_ch

        self._task = asyncio.create_task(self._main_task())
        self._task.add_done_callback(lambda _: self._event_ch.close())

    @abstractmethod
    async def _main_task(self) -> None: ...

    def push_frame(self, frame: AudioFrame) -> None:
        """
        Push an audio frame for VAD processing.
        
        Args:
            frame: An AudioFrame object containing audio data to be analyzed.
        """
        self._check_input_not_ended()
        self._check_not_closed()
        self._input_ch.send_nowait(frame)

    def flush(self) -> None:
        """Mark the end of the current segment"""
        self._check_input_not_ended()
        self._check_not_closed()
        self._input_ch.send_nowait(self._FlushSentinel())

    def end_input(self) -> None:
        """Mark the end of input, no more text will be pushed"""
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
                raise exc  # noqa: B904

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
