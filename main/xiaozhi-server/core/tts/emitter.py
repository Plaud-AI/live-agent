"""
Audio Emitter - Audio Frame Management and Emission

Manages audio frame buffering, segmentation, and duration tracking for the TTS pipeline.
This component converts raw audio bytes from TTS into standardized AudioFrame objects
and emits them as SynthesizedAudio events.

Current Design Assumptions:
- Input audio format: Raw PCM (int16, little-endian)
- All TTS providers are expected to output PCM directly
- No audio decoding (MP3/Opus/AAC) is performed in this version

Future Enhancement:
- Add mime_type parameter to initialize() to support encoded audio formats
- Implement audio decoder integration for non-PCM formats
- Support multiple TTS providers with different output formats
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from config.logger import setup_logging
from core.audio.audio_frame import AudioFrame
from core.providers.tts.base import SynthesizedAudio
from core.utils.aio import Chan, cancel_and_wait

if TYPE_CHECKING:
    pass

logger = setup_logging()


class AudioEmitter:
    """
    Audio emitter for managing audio frame generation and emission.
    
    This class:
    1. Buffers raw audio bytes into frames (default 200ms chunks)
    2. Tracks audio duration for each segment
    3. Manages segment lifecycle (start/end)
    4. Emits SynthesizedAudio events with metadata
    """
    
    class _FlushSegment:
        """Sentinel to flush current frame buffer"""
        pass

    @dataclass
    class _StartSegment:
        """Sentinel to start a new segment"""
        segment_id: str

    class _EndSegment:
        """Sentinel to end current segment"""
        pass

    @dataclass
    class _SegmentContext:
        """Context for tracking segment state"""
        segment_id: str
        audio_duration: float = 0.0

    def __init__(
        self,
        *,
        label: str,
        dst_ch: Chan[SynthesizedAudio],
    ) -> None:
        """
        Initialize the audio emitter.
        
        Args:
            label: Label for logging and debugging
            dst_ch: Destination channel for SynthesizedAudio events
        """
        self._dst_ch = dst_ch
        self._label = label
        self._request_id: str = ""
        self._started = False
        self._num_segments = 0
        self._audio_durations: list[float] = []  # Track durations per segment

    def pushed_duration(self, idx: int = -1) -> float:
        """
        Get the total audio duration for a specific segment.
        
        Args:
            idx: Segment index (-1 for latest, default)
            
        Returns:
            float: Total audio duration in seconds
        """
        return (
            self._audio_durations[idx]
            if -len(self._audio_durations) <= idx < len(self._audio_durations)
            else 0.0
        )

    @property
    def num_segments(self) -> int:
        """Get the number of segments processed"""
        return self._num_segments

    def initialize(
        self,
        *,
        request_id: str,
        sample_rate: int,
        num_channels: int,
        frame_size_ms: int = 200,
        stream: bool = False,
    ) -> None:
        """
        Initialize the emitter for a new synthesis request.
        
        Note: This version assumes input is raw PCM (int16). 
        Future versions may add mime_type parameter for encoded audio support.
        
        Args:
            request_id: Unique identifier for this request
            sample_rate: Audio sample rate (e.g., 16000, 24000)
            num_channels: Number of audio channels (1=mono, 2=stereo)
            frame_size_ms: Size of each audio frame in milliseconds (default 200ms)
            stream: Whether this is a streaming synthesis
        """
        if self._started:
            raise RuntimeError("AudioEmitter already started")

        if not request_id:
            logger.bind(tag=__name__).warning(f"No request_id provided for TTS {self._label}")
            request_id = "unknown"

        self._started = True
        self._request_id = request_id
        self._frame_size_ms = frame_size_ms
        self._sample_rate = sample_rate
        self._num_channels = num_channels
        self._streaming = stream

        # Create write channel for audio data
        self._write_ch = Chan[
            Union[
                bytes,
                AudioEmitter._FlushSegment,
                AudioEmitter._StartSegment,
                AudioEmitter._EndSegment,
            ]
        ]()
        self._main_atask = asyncio.create_task(self._main_task(), name="AudioEmitter._main_task")

        if not self._streaming:
            self.__start_segment(segment_id="")  # Always start a segment with stream=False

    def start_segment(self, *, segment_id: str) -> None:
        """
        Start a new audio segment (streaming only).
        
        Args:
            segment_id: Unique identifier for this segment
        """
        if not self._streaming:
            raise RuntimeError(
                "start_segment() can only be called when initialized with stream=True"
            )
        return self.__start_segment(segment_id=segment_id)

    def __start_segment(self, *, segment_id: str) -> None:
        """Internal method to start a new segment"""
        if not self._started:
            raise RuntimeError("AudioEmitter isn't started")

        if self._write_ch.closed:
            return

        self._num_segments += 1
        self._write_ch.send_nowait(self._StartSegment(segment_id=segment_id))

    def end_segment(self) -> None:
        """End the current audio segment (streaming only)"""
        if not self._streaming:
            raise RuntimeError(
                "end_segment() can only be called when initialized with stream=True"
            )
        return self.__end_segment()

    def __end_segment(self) -> None:
        """Internal method to end current segment"""
        if not self._started:
            raise RuntimeError("AudioEmitter isn't started")

        if self._write_ch.closed:
            return

        self._write_ch.send_nowait(self._EndSegment())

    def push(self, data: bytes) -> None:
        """
        Push raw audio data to the emitter.
        
        Args:
            data: Raw PCM audio bytes (int16)
        """
        if not self._started:
            raise RuntimeError("AudioEmitter isn't started")

        if self._write_ch.closed:
            return

        self._write_ch.send_nowait(data)

    def flush(self) -> None:
        """Flush any buffered audio frames"""
        if not self._started:
            raise RuntimeError("AudioEmitter isn't started")

        if self._write_ch.closed:
            return

        self._write_ch.send_nowait(self._FlushSegment())

    def end_input(self) -> None:
        """Mark the end of input and close the write channel"""
        if not self._started:
            raise RuntimeError("AudioEmitter isn't started")

        if self._write_ch.closed:
            return

        self.__end_segment()
        self._write_ch.close()

    async def join(self) -> None:
        """Wait for all audio frames to be emitted"""
        if not self._started:
            raise RuntimeError("AudioEmitter isn't started")

        await self._main_atask

    async def aclose(self) -> None:
        """Close the emitter and cleanup resources"""
        if not self._started:
            return

        # Use cancel_and_wait for proper task cancellation
        await cancel_and_wait(self._main_atask)

    async def _main_task(self) -> None:
        """
        Main task to process audio data and emit frames.
        
        This task:
        1. Buffers raw PCM audio bytes
        2. Creates AudioFrame objects at frame_size_ms intervals
        3. Emits SynthesizedAudio events with metadata
        4. Tracks audio duration per segment
        """
        segment_ctx: AudioEmitter._SegmentContext | None = None
        last_frame: AudioFrame | None = None
        audio_buffer = bytearray()
        
        # Calculate frame size in bytes
        bytes_per_sample = 2  # int16 PCM
        samples_per_frame = int(self._sample_rate * self._frame_size_ms / 1000)
        frame_size_bytes = samples_per_frame * self._num_channels * bytes_per_sample

        def _emit_frame(frame: AudioFrame | None = None, *, is_final: bool = False) -> None:
            """Emit an audio frame as SynthesizedAudio event"""
            nonlocal last_frame, segment_ctx
            assert segment_ctx is not None

            if last_frame is None:
                if not is_final:
                    last_frame = frame
                    return
                elif segment_ctx.audio_duration > 0:
                    # Create a small silent frame if ending without audio
                    if frame is None:
                        silence_samples = self._sample_rate // 100  # 10ms
                        silence_data = b"\0\0" * (silence_samples * self._num_channels)
                        frame = AudioFrame(
                            audio_data=silence_data,
                            sample_rate=self._sample_rate,
                            num_channels=self._num_channels,
                            samples_per_channel=silence_samples,
                        )
                    else:
                        segment_ctx.audio_duration += frame.duration
                        self._audio_durations[-1] += frame.duration

                    self._dst_ch.send_nowait(
                        SynthesizedAudio(
                            frame=frame,
                            request_id=self._request_id,
                            segment_id=segment_ctx.segment_id,
                            is_final=True,
                        )
                    )
                    return

            if last_frame is not None:
                self._dst_ch.send_nowait(
                    SynthesizedAudio(
                        frame=last_frame,
                        request_id=self._request_id,
                        segment_id=segment_ctx.segment_id,
                        is_final=is_final,
                    )
                )
                segment_ctx.audio_duration += last_frame.duration
                self._audio_durations[-1] += last_frame.duration

            last_frame = frame

        def _flush_frame() -> None:
            """Flush the last buffered frame"""
            nonlocal last_frame, segment_ctx
            assert segment_ctx is not None

            if last_frame is None:
                return

            self._dst_ch.send_nowait(
                SynthesizedAudio(
                    frame=last_frame,
                    request_id=self._request_id,
                    segment_id=segment_ctx.segment_id,
                    is_final=False,
                )
            )
            segment_ctx.audio_duration += last_frame.duration
            self._audio_durations[-1] += last_frame.duration
            last_frame = None

        try:
            async for data in self._write_ch:
                if isinstance(data, AudioEmitter._StartSegment):
                    if segment_ctx:
                        raise RuntimeError(
                            "start_segment() called before the previous segment was ended"
                        )

                    self._audio_durations.append(0.0)
                    segment_ctx = AudioEmitter._SegmentContext(segment_id=data.segment_id)
                    audio_buffer.clear()
                    continue

                if not segment_ctx:
                    if self._streaming:
                        if isinstance(data, (AudioEmitter._EndSegment, AudioEmitter._FlushSegment)):
                            continue  # Empty segment, ignore

                        raise RuntimeError(
                            "start_segment() must be called before pushing audio data"
                        )

                if isinstance(data, bytes):
                    # Buffer audio data
                    audio_buffer.extend(data)

                    # Create frames while we have enough data
                    while len(audio_buffer) >= frame_size_bytes:
                        frame_data = bytes(audio_buffer[:frame_size_bytes])
                        audio_buffer = audio_buffer[frame_size_bytes:]

                        frame = AudioFrame(
                            audio_data=frame_data,
                            sample_rate=self._sample_rate,
                            num_channels=self._num_channels,
                            samples_per_channel=samples_per_frame,
                        )
                        _emit_frame(frame)

                elif isinstance(data, AudioEmitter._FlushSegment):
                    # Flush remaining buffer
                    if audio_buffer:
                        # Pad to complete frame if needed
                        remaining = len(audio_buffer)
                        if remaining > 0:
                            samples = remaining // (self._num_channels * bytes_per_sample)
                            frame = AudioFrame(
                                audio_data=bytes(audio_buffer),
                                sample_rate=self._sample_rate,
                                num_channels=self._num_channels,
                                samples_per_channel=samples,
                            )
                            _emit_frame(frame)
                        audio_buffer.clear()
                    _flush_frame()

                elif isinstance(data, AudioEmitter._EndSegment) and segment_ctx:
                    # End current segment
                    if audio_buffer:
                        samples = len(audio_buffer) // (self._num_channels * bytes_per_sample)
                        frame = AudioFrame(
                            audio_data=bytes(audio_buffer),
                            sample_rate=self._sample_rate,
                            num_channels=self._num_channels,
                            samples_per_channel=samples,
                        )
                        _emit_frame(frame)
                        audio_buffer.clear()

                    _emit_frame(is_final=True)
                    segment_ctx = last_frame = None

        except Exception as e:
            logger.bind(tag=__name__).error(f"AudioEmitter error: {e}")
            raise
        finally:
            # Cleanup
            if segment_ctx and last_frame:
                _emit_frame(is_final=True)

