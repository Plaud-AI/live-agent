from __future__ import annotations

import asyncio

from dataclasses import dataclass
from typing import Callable, Any, Union, AsyncIterator
from types import TracebackType
from abc import ABC, abstractmethod
import core.audio as audio

# ============================================================================
# TTS Stream Basic Data Structures
# ============================================================================
@dataclass
class SynthesizedAudio:
    """
    Represents synthesized audio output from the TTS pipeline.
    
    This is the standard output format for the streaming TTS pipeline,
    containing audio data along with metadata for tracking and synchronization.
    
    Attributes:
        frame: The audio frame containing PCM audio data
        request_id: Unique identifier for the TTS request
        segment_id: Unique identifier for the segment (multiple frames can belong to one segment)
        is_final: Whether this is the final frame of the current segment
        delta_text: The text fragment corresponding to this audio frame (for subtitle sync)
    """
    frame: audio.AudioFrame
    request_id: str
    segment_id: str = ""
    is_final: bool = False
    delta_text: str = ""


@dataclass
class TTSCapabilities:
    """TTS capabilities descriptor"""
    streaming: bool
    """Whether this TTS supports streaming (generally using websockets)"""


# ============================================================================
# TTS Base Classes
# ============================================================================

class TTS(ABC):
    """
    Base class for Text-to-Speech providers.
    
    This is a modern, async-first TTS interface inspired by LiveKit's design.
    Providers should inherit from this class and implement the required methods.
    """
    
    def __init__(
        self,
        *,
        capabilities: TTSCapabilities,
        sample_rate: int,
        num_channels: int,
    ) -> None:
        """
        Initialize TTS provider.
        
        Args:
            capabilities: TTS capabilities (streaming support, etc.)
            sample_rate: Audio sample rate (e.g., 16000, 24000)
            num_channels: Number of audio channels (1=mono, 2=stereo)
        """
        self._capabilities = capabilities
        self._sample_rate = sample_rate
        self._num_channels = num_channels
        self._label = f"{type(self).__module__}.{type(self).__name__}"
    
    @property
    def label(self) -> str:
        """Get the TTS provider label (module.ClassName)"""
        return self._label
    
    @property
    def model(self) -> str:
        """
        Get the model name/identifier for this TTS instance.
        
        Returns:
            The model name if available, "unknown" otherwise.
        
        Note:
            Providers should override this property to provide their model information.
        """
        return "unknown"
    
    @property
    def provider(self) -> str:
        """
        Get the provider name/identifier for this TTS instance.
        
        Returns:
            The provider name if available, "unknown" otherwise.
        
        Note:
            Providers should override this property to provide their provider information.
        """
        return "unknown"
    
    @property
    def capabilities(self) -> TTSCapabilities:
        """Get TTS capabilities"""
        return self._capabilities
    
    @property
    def sample_rate(self) -> int:
        """Get audio sample rate"""
        return self._sample_rate
    
    @property
    def num_channels(self) -> int:
        """Get number of audio channels"""
        return self._num_channels
    
    @abstractmethod
    def synthesize(self, text: str) -> 'ChunkedStream':
        """
        Synthesize speech from text (non-streaming).
        
        This method creates a stream that synthesizes the entire text at once.
        The text is provided upfront and cannot be modified during synthesis.
        
        Args:
            text: The text to synthesize
        
        Returns:
            ChunkedStream: An async iterator that yields SynthesizedAudio frames
        """
        ...
    
    def stream(self) -> 'SynthesizeStream':
        """
        Create a streaming synthesis session.
        
        This method creates a stream that allows text to be pushed incrementally.
        Text can be added via push_text() and the stream will synthesize as text arrives.
        
        Returns:
            SynthesizeStream: A streaming synthesis session
        
        Raises:
            NotImplementedError: If streaming is not supported by this TTS
        """
        raise NotImplementedError(
            "streaming is not supported by this TTS, "
            "please use a different TTS or use a StreamAdapter"
        )
    
    def prewarm(self) -> None:
        """
        Pre-warm connection to the TTS service.
        
        This method can be called to establish connections or initialize
        resources before actual synthesis begins, reducing latency.
        """
        pass
    
    async def aclose(self) -> None:
        """
        Close the TTS provider and cleanup resources.
        
        This method should be called when the TTS provider is no longer needed.
        It should close any open connections, cancel pending tasks, and release resources.
        """
        pass
    
    async def __aenter__(self) -> 'TTS':
        return self
    
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.aclose()


class ChunkedStream(ABC):
    """
    Base class for non-streaming synthesis (synthesize full text at once).
    
    This class handles the orchestration of:
    1. Creating an AudioEmitter
    2. Calling the provider's _run() method to synthesize
    3. Managing the output event channel
    4. Cleanup and error handling
    
    Providers should inherit from this class and implement _run().
    """
    
    def __init__(
        self,
        *,
        tts: TTS,
        input_text: str,
    ) -> None:
        """
        Initialize ChunkedStream.
        
        Args:
            tts: The TTS provider instance
            input_text: The text to synthesize
        """
        from core.utils.aio import Chan
        
        self._input_text = input_text
        self._tts = tts
        self._event_ch: Chan[SynthesizedAudio] = Chan()
        self._synthesize_task = asyncio.create_task(
            self._main_task(), 
            name="ChunkedStream._main_task"
        )
        self._synthesize_task.add_done_callback(lambda _: self._event_ch.close())
    
    @property
    def input_text(self) -> str:
        """Get the input text"""
        return self._input_text
    
    @property
    def done(self) -> bool:
        """Check if synthesis is complete"""
        return self._synthesize_task.done()
    
    @property
    def exception(self) -> BaseException | None:
        """Get exception if synthesis failed"""
        return self._synthesize_task.exception()
    
    @abstractmethod
    async def _run(self, output_emitter: Any) -> None:
        """
        Provider-specific synthesis implementation.
        
        This method should:
        1. Initialize the output_emitter
        2. Call the TTS API to synthesize the input text
        3. Push audio data to output_emitter using output_emitter.push()
        4. Call output_emitter.flush() when done
        
        Args:
            output_emitter: AudioEmitter to push synthesized audio to
        """
        ...
    
    async def _main_task(self) -> None:
        """Main task to orchestrate synthesis"""
        from .emitter import AudioEmitter
        
        output_emitter = AudioEmitter(label=self._tts.label, dst_ch=self._event_ch)
        try:
            await self._run(output_emitter)
            output_emitter.end_input()
            await output_emitter.join()
        finally:
            await output_emitter.aclose()
    
    async def collect(self) -> audio.AudioFrame:
        """
        Utility method to collect all frames into a single AudioFrame.
        
        Returns:
            Combined AudioFrame containing all synthesized audio
        """
        frames = []
        async for ev in self:
            frames.append(ev.frame)
        
        return audio.AudioFrame.combine_frames(frames)
    
    async def aclose(self) -> None:
        """Close the stream and cleanup resources"""
        from core.utils.aio import cancel_and_wait
        
        await cancel_and_wait(self._synthesize_task)
        self._event_ch.close()
    
    async def __anext__(self) -> SynthesizedAudio:
        try:
            val = await self._event_ch.recv()
        except Exception:
            # Check if there was an exception in the synthesis task
            if not self._synthesize_task.cancelled() and (exc := self._synthesize_task.exception()):
                raise exc
            raise StopAsyncIteration from None
        
        return val
    
    def __aiter__(self) -> AsyncIterator[SynthesizedAudio]:
        return self
    
    async def __aenter__(self) -> 'ChunkedStream':
        return self
    
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.aclose()


class SynthesizeStream(ABC):
    """
    Base class for streaming synthesis (push text incrementally).
    
    This class handles:
    1. Input text channel (for incremental text input)
    2. Output audio channel (for synthesized audio)
    3. Orchestration of AudioEmitter
    4. Flush/end_input semantics
    
    Providers should inherit from this class and implement _run().
    """
    
    class _FlushSentinel:
        """Sentinel to mark segment boundaries"""
        pass
    
    def __init__(self, *, tts: TTS) -> None:
        """
        Initialize SynthesizeStream.
        
        Args:
            tts: The TTS provider instance
        """
        from core.utils.aio import Chan
        
        self._tts = tts
        self._input_ch: Chan[Union[str, SynthesizeStream._FlushSentinel]] = Chan()
        self._event_ch: Chan[SynthesizedAudio] = Chan()
        
        self._task = asyncio.create_task(self._main_task(), name="SynthesizeStream._main_task")
        self._task.add_done_callback(lambda _: self._event_ch.close())
    
    @abstractmethod
    async def _run(self, output_emitter: Any) -> None:
        """
        Provider-specific streaming synthesis implementation.
        
        This method should:
        1. Initialize output_emitter
        2. Create tokenizer/pacer (if needed)
        3. Set up parallel tasks to:
           - Read from self._input_ch and feed to tokenizer
           - Process tokenized text and call TTS API
           - Push audio from TTS to output_emitter
        
        Args:
            output_emitter: AudioEmitter to push synthesized audio to
        """
        ...
    
    async def _main_task(self) -> None:
        """Main task to orchestrate streaming synthesis"""
        from .emitter import AudioEmitter
        
        output_emitter = AudioEmitter(label=self._tts.label, dst_ch=self._event_ch)
        try:
            await self._run(output_emitter)
            output_emitter.end_input()
            await output_emitter.join()
        finally:
            await output_emitter.aclose()
    
    def push_text(self, token: str) -> None:
        """
        Push a text fragment to be synthesized.
        
        Text fragments will be accumulated and processed according to
        the tokenizer/pacer configuration (if any).
        
        Args:
            token: Text fragment to synthesize
        """
        if not token or self._input_ch.closed:
            return
        
        self._input_ch.send_nowait(token)
    
    def flush(self) -> None:
        """
        Mark the end of the current segment.
        
        This signals that all text for the current segment has been pushed.
        The TTS will finish synthesizing the current segment before starting the next.
        """
        if self._input_ch.closed:
            return
        
        self._input_ch.send_nowait(self._FlushSentinel())
    
    def end_input(self) -> None:
        """
        Mark the end of input.
        
        This signals that no more text will be pushed. The TTS will finish
        synthesizing any remaining text and close the stream.
        """
        self.flush()
        self._input_ch.close()
    
    async def aclose(self) -> None:
        """Close the stream immediately and cleanup resources"""
        from core.utils.aio import cancel_and_wait
        
        await cancel_and_wait(self._task)
        self._event_ch.close()
        self._input_ch.close()
    
    async def __anext__(self) -> SynthesizedAudio:
        try:
            val = await self._event_ch.recv()
        except Exception:
            if not self._task.cancelled() and (exc := self._task.exception()):
                raise exc
            raise StopAsyncIteration from None
        
        return val
    
    def __aiter__(self) -> AsyncIterator[SynthesizedAudio]:
        return self
    
    async def __aenter__(self) -> 'SynthesizeStream':
        return self
    
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.aclose()


# Factory function for creating TTS instances from configuration

async def create_from_config(config, audio_params) -> TTS:
    """
    Factory function to create TTS instance from configuration.
    
    Args:
        config: TTS configuration object (from config.components.tts)
        audio_params: Audio parameters with sample_rate, channels, format
        
    Returns:
        Initialized TTS instance
        
    Raises:
        ValueError: If the specified provider is not supported
        
    Example:
        config = load_config("config.yaml")
        tts = await create_from_config(config.components.tts, config.audio_params)
    """
    import logging
    
    provider = config.provider.lower()
    logging.info(f"Creating TTS: provider={provider}, model={config.model.name}")
    
    if provider == "elevenlabs":
        from core.tts.elevenlabs.tts import TTS as ElevenLabsTTS
        return await ElevenLabsTTS.from_config(config, audio_params)
    elif provider == "cartesia":
        from core.tts.cartesia.tts import TTS as CartesiaTTS
        return await CartesiaTTS.from_config(config, audio_params)
    else:
        raise ValueError(f"Unsupported TTS provider: {provider}")
