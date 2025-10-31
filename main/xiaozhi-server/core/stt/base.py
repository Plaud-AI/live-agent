"""
Base class for Speech To Text (STT) providers.

This is a modern, async-first STT interface inspired by LiveKit's design.
Providers should inherit from this class and implement the required methods.
"""
from __future__ import annotations
import asyncio
import logging
from abc import ABC, abstractmethod    
from dataclasses import dataclass, field
from enum import Enum, unique
from types import TracebackType
from typing import Literal, Union, Any, TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field
from collections.abc import AsyncIterator
from core.audio.audio_frame import AudioFrame
from core.utils.aio import Chan, cancel_and_wait
from core.utils.types import (
    APIConnectOptions,
    DEFAULT_API_CONNECT_OPTIONS,
    NOT_GIVEN,
    NotGivenOr,
    is_given,
)
from core.utils.errors import APIConnectionError, APIError
from core.utils.short_uuid import shortuuid

# Type alias for audio buffer
AudioBuffer = Union[list[AudioFrame], AudioFrame]

# Type alias for VAD (to avoid circular imports)
# Providers should import VAD from their respective modules
if TYPE_CHECKING:
    VAD = Any
else:
    VAD = None


@unique
class SpeechEventType(str, Enum):
    START_OF_SPEECH = "start_of_speech"
    """indicate the start of speech
    if the STT doesn't support this event, this will be emitted as the same time as the first INTERIM_TRANSCRIPT"""
    INTERIM_TRANSCRIPT = "interim_transcript"
    """interim transcript, useful for real-time transcription"""
    PREFLIGHT_TRANSCRIPT = "preflight_transcript"
    """preflight transcript, emitted when the STT is confident enough that a certain
    portion of speech will not change. This is different from final transcript in that
    the same transcript may still be updated; but it is stable enough to be used for
    preemptive generation"""
    FINAL_TRANSCRIPT = "final_transcript"
    """final transcript, emitted when the STT is confident enough that a certain
    portion of speech will not change"""
    RECOGNITION_USAGE = "recognition_usage"
    """usage event, emitted periodically to indicate usage metrics"""
    END_OF_SPEECH = "end_of_speech"
    """indicate the end of speech, emitted when the user stops speaking"""


@dataclass
class SpeechData:
    language: str
    text: str
    start_time: float = 0.0
    end_time: float = 0.0
    confidence: float = 0.0  # [0, 1]
    speaker_id: str | None = None
    is_primary_speaker: bool | None = None


@dataclass
class RecognitionUsage:
    audio_duration: float


@dataclass
class SpeechEvent:
    type: SpeechEventType
    request_id: str = ""
    alternatives: list[SpeechData] = field(default_factory=list)
    recognition_usage: RecognitionUsage | None = None


@dataclass
class STTCapabilities:
    streaming: bool
    interim_results: bool


class STTError(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    type: Literal["stt_error"] = "stt_error"
    timestamp: float
    label: str
    error: Exception = Field(..., exclude=True)
    recoverable: bool


class STT(ABC):
    """
    Base class for Speech-to-Text (STT) providers.
    
    This is a modern, async-first STT interface inspired by LiveKit's design.
    Providers should inherit from this class and implement the required methods.
    """
    
    def __init__(self, *, capabilities: STTCapabilities) -> None:
        """
        Initialize STT provider.
        
        Args:
            capabilities: STT capabilities (streaming support, interim results, etc.)
        """
        self._capabilities = capabilities
        self._label = f"{type(self).__module__}.{type(self).__name__}"
    
    @property
    def label(self) -> str:
        """Get the STT provider label (module.ClassName)"""
        return self._label
    
    @property
    def model(self) -> str:
        """
        Get the model name/identifier for this STT instance.
        
        Returns:
            The model name if available, "unknown" otherwise.
        
        Note:
            Providers should override this property to provide their model information.
        """
        return "unknown"
    
    @property
    def provider(self) -> str:
        """
        Get the provider name/identifier for this STT instance.
        
        Returns:
            The provider name if available, "unknown" otherwise.
        
        Note:
            Providers should override this property to provide their provider information.
        """
        return "unknown"
    
    @property
    def capabilities(self) -> STTCapabilities:
        """Get STT capabilities"""
        return self._capabilities
    
    @abstractmethod
    async def _recognize_impl(
        self,
        buffer: AudioBuffer,
        *,
        language: NotGivenOr[str] = NOT_GIVEN,
        conn_options: APIConnectOptions,
    ) -> SpeechEvent:
        """
        Provider-specific recognition implementation.
        
        This method should be implemented by STT providers to perform
        the actual speech recognition on the provided audio buffer.
        
        Args:
            buffer: Audio buffer (list of AudioFrame or single AudioFrame)
            language: Optional language code for recognition
            conn_options: Connection options for API calls
        
        Returns:
            SpeechEvent: Recognition result with transcript and metadata
        """
        ...
    
    async def recognize(
        self,
        buffer: AudioBuffer,
        *,
        language: NotGivenOr[str] = NOT_GIVEN,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> SpeechEvent:
        """
        Recognize speech from audio buffer (non-streaming).
        
        This method provides retry logic and error handling around _recognize_impl().
        
        Args:
            buffer: Audio buffer (list of AudioFrame or single AudioFrame)
            language: Optional language code for recognition
            conn_options: Connection options for API calls
        
        Returns:
            SpeechEvent: Recognition result with transcript and metadata
        """
        for i in range(conn_options.max_retry + 1):
            try:
                event = await self._recognize_impl(
                    buffer, language=language, conn_options=conn_options
                )
                return event
            
            except APIError as e:
                retry_interval = conn_options.retry_interval
                if conn_options.max_retry == 0:
                    self._emit_error(e, recoverable=False)
                    raise
                elif i == conn_options.max_retry:
                    self._emit_error(e, recoverable=False)
                    raise APIConnectionError(
                        f"failed to recognize speech after {conn_options.max_retry + 1} attempts"
                    ) from e
                else:
                    self._emit_error(e, recoverable=True)
                    logging.warning(
                        f"failed to recognize speech, retrying in {retry_interval}s",
                        exc_info=e,
                        extra={
                            "asr": self._label,
                            "attempt": i + 1,
                            "streamed": False,
                        },
                    )
                
                await asyncio.sleep(retry_interval)
            
            except Exception as e:
                self._emit_error(e, recoverable=False)
                raise
        
        raise RuntimeError("unreachable")
    
    def _emit_error(self, api_error: Exception, recoverable: bool) -> None:
        """Emit an error event (placeholder for future event emitter support)"""
        logging.error(
            f"STT error: {api_error}",
            extra={"asr": self._label, "recoverable": recoverable},
            exc_info=api_error,
        )
    
    def stream(
        self,
        *,
        language: NotGivenOr[str] = NOT_GIVEN,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> "RecognizeStream":
        """
        Create a streaming recognition session.
        
        This method creates a stream that allows audio frames to be pushed incrementally.
        Audio frames can be added via push_frame() and the stream will transcribe as audio arrives.
        
        Args:
            language: Optional language code for recognition (e.g., "en", "zh", "multi")
            conn_options: Connection options for the API (timeout, retry, etc.)
        
        Returns:
            RecognizeStream: A streaming recognition session
        
        Raises:
            NotImplementedError: If streaming is not supported by this STT
        """
        raise NotImplementedError(
            "streaming is not supported by this STT, "
            "please use a different STT or use a StreamAdapter"
        )
    
    def prewarm(self) -> None:
        """
        Pre-warm connection to the STT service.
        
        This method can be called to establish connections or initialize
        resources before actual recognition begins, reducing latency.
        """
        pass
    
    async def aclose(self) -> None:
        """
        Close the STT provider and clean up resources.

        This method should be called when the STT provider is no longer needed.
        It will close all active streams and release any held resources.
        """
        pass
    
    async def __aenter__(self) -> "STT":
        return self
    
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.aclose()


class RecognizeStream(ABC):
    """
    Base class for streaming recognition (push audio frames incrementally).
    
    This class handles:
    1. Input audio frame channel (for incremental audio input)
    2. Output speech event channel (for recognition results)
    3. Flush/end_input semantics
    4. Error handling and retry logic
    
    Providers should inherit from this class and implement _run().
    """
    
    class _FlushSentinel:
        """Sentinel to mark segment boundaries"""
        pass
    
    def __init__(
        self,
        *,
        stt: STT,
        conn_options: APIConnectOptions,
        sample_rate: NotGivenOr[int] = NOT_GIVEN,
        language: NotGivenOr[str] = NOT_GIVEN,
    ) -> None:
        """
        Initialize RecognizeStream.
        
        Args:
            stt: The STT provider instance
            conn_options: Connection options for API calls
            sample_rate: Optional desired sample rate (for future resampling support)
            language: Optional language code for recognition
        """
        self._stt = stt
        self._conn_options = conn_options
        self._language = language
        self._needed_sr = sample_rate if is_given(sample_rate) else None
        self._pushed_sr = 0
        
        self._input_ch: Chan[Union[AudioFrame, RecognizeStream._FlushSentinel]] = Chan()
        self._event_ch: Chan[SpeechEvent] = Chan()
        
        # TODO: If metrics monitoring is needed in the future, the event channel should be teed
        #       to allow multiple consumers (main stream and metrics monitor)
        #       Example: self._event_aiter, monitor_aiter = tee(self._event_ch, 2)
        self._event_aiter = self._event_ch
        self._task = asyncio.create_task(self._main_task(), name="RecognizeStream._main_task")
        self._task.add_done_callback(lambda _: self._event_ch.close())
        
        self._num_retries = 0
    
    @abstractmethod
    async def _run(self) -> None:
        """
        Provider-specific streaming recognition implementation.
        
        This method should:
        1. Set up parallel tasks to:
           - Read from self._input_ch and process audio frames
           - Call STT API and push recognition results to self._event_ch
           - Handle flush signals and end_of_input
        
        The method should push SpeechEvent objects to self._event_ch as recognition
        results become available.
        """
        ...
    
    async def _main_task(self) -> None:
        """Main task to orchestrate streaming recognition with retry logic"""
        max_retries = self._conn_options.max_retry
        
        while self._num_retries <= max_retries:
            try:
                return await self._run()
            except APIError as e:
                if max_retries == 0:
                    self._emit_error(e, recoverable=False)
                    raise
                elif self._num_retries == max_retries:
                    self._emit_error(e, recoverable=False)
                    raise APIConnectionError(
                        f"failed to recognize speech after {self._num_retries + 1} attempts"
                    ) from e
                else:
                    self._emit_error(e, recoverable=True)
                    
                    retry_interval = self._conn_options.retry_interval
                    logging.warning(
                        f"failed to recognize speech, retrying in {retry_interval}s",
                        extra={
                            "stt": self._stt._label,
                            "attempt": self._num_retries + 1,
                            "streamed": True,
                        },
                    )
                    await asyncio.sleep(retry_interval)
                
                self._num_retries += 1
            
            except Exception as e:
                self._emit_error(e, recoverable=False)
                raise
    
    def _emit_error(self, api_error: Exception, recoverable: bool) -> None:
        """Emit an error event (placeholder for future event emitter support)"""
        logging.error(
            f"STT error: {api_error}",
            extra={"stt": self._stt._label, "recoverable": recoverable},
            exc_info=api_error,
        )
    
    def push_frame(self, frame: AudioFrame) -> None:
        """Push audio frame to be recognized"""
        self._check_input_not_ended()
        self._check_not_closed()
        
        if self._pushed_sr and self._pushed_sr != frame.sample_rate:
            raise ValueError("the sample rate of the input frames must be consistent")
        
        self._pushed_sr = frame.sample_rate
        
        # TODO: Implement resampling if _needed_sr is set and differs from frame.sample_rate
        # For now, just pass through the frame
        
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
    
    async def __anext__(self) -> SpeechEvent:
        try:
            val = await self._event_aiter.__anext__()
        except StopAsyncIteration:
            if not self._task.cancelled() and (exc := self._task.exception()):
                raise exc
            
            raise StopAsyncIteration from None
        
        return val
    
    def __aiter__(self) -> AsyncIterator[SpeechEvent]:
        return self
    
    def _check_not_closed(self) -> None:
        if self._event_ch.closed:
            cls = type(self)
            raise RuntimeError(f"{cls.__module__}.{cls.__name__} is closed")
    
    def _check_input_not_ended(self) -> None:
        if self._input_ch.closed:
            cls = type(self)
            raise RuntimeError(f"{cls.__module__}.{cls.__name__} input ended")
    
    async def __aenter__(self) -> "RecognizeStream":
        return self
    
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.aclose()


class StreamAdapter(STT):
    """
    Wrap a non-streaming STT to provide streaming interface.
    
    This adapter enables any STT that supports non-streaming recognition
    (via speech_to_text method) to be used with the streaming API.
    It handles:
    - Audio frame buffering
    - VAD-based segmentation (when VAD is available)
    - Sequential recognition of audio segments
    - Streaming recognition results
    
    Example:
        # Wrap a non-streaming STT
        base_stt = SomeSTT(...)
        streaming_stt = StreamAdapter(
            stt=base_stt,
            vad=vad_instance  # Optional VAD for segmentation
        )
        
        # Now use it as a streaming STT
        stream = streaming_stt.stream()
        stream.push_frame(frame1)
        stream.push_frame(frame2)
        stream.end_input()
        
        async for event in stream:
            # Process recognition events
            pass
    """
    
    def __init__(
        self,
        *,
        stt: STT,
        vad: VAD | None = None,
    ) -> None:
        """
        Initialize StreamAdapter.
        
        Args:
            stt: The non-streaming STT to wrap
            vad: Optional VAD for automatic segmentation.
                 If provided, VAD will be used to detect speech boundaries.
                 If not provided, manual flush() calls are required.
        """
        super().__init__(
            capabilities=STTCapabilities(
                streaming=True,
                interim_results=False,  # Non-streaming STT doesn't support interim results
            )
        )
        self._wrapped_stt = stt
        self._vad = vad
    
    @property
    def model(self) -> str:
        """Get the model from wrapped STT"""
        return self._wrapped_stt.model
    
    @property
    def provider(self) -> str:
        """Get the provider from wrapped STT"""
        return self._wrapped_stt.provider
    
    def stream(
        self,
        *,
        language: NotGivenOr[str] = NOT_GIVEN,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> "StreamAdapterWrapper":
        """
        Create a streaming recognition session.
        
        Args:
            language: Optional language code for recognition
            conn_options: Connection options for API calls
        
        Returns:
            StreamAdapterWrapper: A streaming wrapper around the non-streaming STT
        """
        return StreamAdapterWrapper(
            asr=self,
            wrapped_stt=self._wrapped_stt,
            vad=self._vad,
            language=language,
            conn_options=conn_options,
        )
    
    async def aclose(self) -> None:
        """Close the wrapped STT"""
        await self._wrapped_stt.aclose()


class StreamAdapterWrapper(RecognizeStream):
    """
    Streaming wrapper that recognizes audio segments sequentially.
    
    This class orchestrates:
    1. Reading audio frames from input channel
    2. Buffering frames until segmentation boundary (VAD or flush)
    3. Calling wrapped STT's recognize for each segment
    4. Streaming recognition results
    """
    
    def __init__(
        self,
        *,
        stt: StreamAdapter,
        wrapped_stt: STT,
        vad: "VAD | None",
        language: NotGivenOr[str],
        conn_options: APIConnectOptions,
    ) -> None:
        """
        Initialize StreamAdapterWrapper.
        
        Args:
            stt: The StreamAdapter instance
            wrapped_stt: The wrapped non-streaming STT
            vad: Optional VAD for segmentation
            language: Optional language code
            conn_options: Connection options
        """
        super().__init__(stt=stt, conn_options=conn_options, language=language)
        self._stream_adapter = stt
        self._wrapped_stt = wrapped_stt
        self._vad = vad
    
    async def _run(self) -> None:
        """
        Main streaming recognition logic.
        
        This method:
        1. Buffers audio frames
        2. Uses VAD (if available) or flush signals to segment audio
        3. Calls wrapped STT for each segment
        4. Streams recognition results
        """
        from core.audio.audio_frame import AudioFrame
        
        request_id = shortuuid("asr_request_")
        audio_buffer: list[AudioFrame] = []
        
        # If VAD is available, use it for segmentation
        if self._vad:
            await self._run_with_vad(request_id, audio_buffer)
        else:
            await self._run_without_vad(request_id, audio_buffer)
    
    async def _run_with_vad(
        self, request_id: str, audio_buffer: list[AudioFrame]
    ) -> None:
        """Run recognition with VAD-based segmentation"""
        # TODO: Implement VAD-based segmentation
        # This will require:
        # 1. Forwarding audio frames to VAD stream
        # 2. Listening for VAD events (START_OF_SPEECH, END_OF_SPEECH)
        # 3. Buffering frames during speech
        # 4. Recognizing complete segments on END_OF_SPEECH
        # 5. StreamAdapter from livekit-agents provides a good reference
        
        raise NotImplementedError(
            "VAD-based segmentation is not yet implemented. "
            "Please use manual flush() calls or implement VAD support."
        )
    
    async def _run_without_vad(
        self, request_id: str, audio_buffer: list[AudioFrame]
    ) -> None:
        """Run recognition with manual flush-based segmentation"""
        from core.audio.audio_frame import AudioFrame
        
        async def _forward_input() -> None:
            """Forward audio frames from input channel to buffer"""
            async for data in self._input_ch:
                if isinstance(data, self._FlushSentinel):
                    # Flush signal - recognize current buffer
                    if audio_buffer:
                        await self._recognize_segment(request_id, audio_buffer)
                        audio_buffer.clear()
                    continue
                
                if isinstance(data, AudioFrame):
                    audio_buffer.append(data)
            
            # End of input - recognize any remaining buffer
            if audio_buffer:
                await self._recognize_segment(request_id, audio_buffer)
        
        await _forward_input()
    
    async def _recognize_segment(
        self, request_id: str, frames: list[AudioFrame]
    ) -> None:
        """
        Recognize a segment of audio frames using the wrapped STT.
        
        Args:
            request_id: Request ID for this recognition segment
            frames: List of audio frames to recognize
        """
        if not frames:
            return
        
        # Use recognize() method from STT base class
        # Convert frames list to AudioBuffer (list[AudioFrame])
        try:
            event = await self._wrapped_stt.recognize(
                buffer=frames,
                language=self._language if is_given(self._language) else NOT_GIVEN,
                conn_options=self._conn_options,
            )
            
            # Update request_id if needed
            if event.request_id != request_id:
                event.request_id = request_id
            
            # Emit the recognition event
            self._event_ch.send_nowait(event)
            
        except Exception as e:
            logging.error(
                f"Recognition failed: {e}",
                extra={
                    "stt": self._wrapped_stt._label,
                    "request_id": request_id,
                },
                exc_info=e,
            )
            raise APIError(f"Recognition failed: {e}") from e


# Factory function for creating STT instances from configuration

async def create_from_config(config) -> STT:
    """
    Factory function to create STT instance from configuration.
    
    Args:
        config: STT configuration object (from config.components.stt)
        
    Returns:
        Initialized STT instance
        
    Raises:
        ValueError: If the specified provider is not supported
        
    Example:
        config = load_config("config.yaml")
        stt = await create_from_config(config.components.stt)
    """
    provider = config.provider.lower()
    logging.info(f"Creating STT: provider={provider}, model={config.model.name}")
    
    if provider == "groq":
        from core.stt.groq.stt import STT as GroqSTT
        return await GroqSTT.from_config(config)
    elif provider == "openai":
        from core.stt.openai.stt import STT as OpenAISTT
        return await OpenAISTT.from_config(config)
    else:
        raise ValueError(f"Unsupported STT provider: {provider}")
