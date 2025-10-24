"""
Audio utilities for handling audio frames and stream processing.

This module provides classes and utilities for working with audio data,
including frame representation and manipulation.
"""

from __future__ import annotations

import ctypes
from typing import Union


class AudioFrame:
    """
    Represents a frame of audio data with specific properties such as sample rate,
    number of channels, and samples per channel.
    
    The format of the audio data is 16-bit signed integers (int16) interleaved by channel.
    
    Example:
        >>> # Create a frame from PCM data
        >>> frame = AudioFrame(
        ...     data=pcm_bytes,
        ...     sample_rate=16000,
        ...     num_channels=1,
        ...     samples_per_channel=960
        ... )
        >>> print(f"Duration: {frame.duration:.3f}s")
        Duration: 0.060s
    """
    
    def __init__(
        self,
        data: Union[bytes, bytearray, memoryview],
        sample_rate: int,
        num_channels: int,
        samples_per_channel: int,
    ) -> None:
        """
        Initialize an AudioFrame instance.
        
        Args:
            data: The raw audio data as 16-bit PCM (int16), must be at least
                `num_channels * samples_per_channel * sizeof(int16)` bytes long.
            sample_rate: The sample rate of the audio in Hz (e.g., 16000, 48000).
            num_channels: The number of audio channels (1 for mono, 2 for stereo).
            samples_per_channel: The number of samples per channel.
            
        Raises:
            ValueError: If the length of data is smaller than the required size.
            ValueError: If the data length is not a multiple of sizeof(int16).
        """
        data = memoryview(data).cast("B")  # Cast to bytes
        
        # Validate data length
        required_size = num_channels * samples_per_channel * ctypes.sizeof(ctypes.c_int16)
        if len(data) < required_size:
            raise ValueError(
                f"data length must be >= num_channels * samples_per_channel * sizeof(int16) "
                f"(expected at least {required_size} bytes, got {len(data)} bytes)"
            )
        
        if len(data) % ctypes.sizeof(ctypes.c_int16) != 0:
            raise ValueError("data length must be a multiple of sizeof(int16)")
        
        # Store data as ctypes array for efficient access
        n = len(data) // ctypes.sizeof(ctypes.c_int16)
        self._data = (ctypes.c_int16 * n).from_buffer_copy(data)
        
        self._sample_rate = sample_rate
        self._num_channels = num_channels
        self._samples_per_channel = samples_per_channel
    
    @staticmethod
    def create(
        sample_rate: int,
        num_channels: int,
        samples_per_channel: int,
    ) -> AudioFrame:
        """
        Create a new empty AudioFrame with specified parameters.
        
        The frame will be initialized with zero-filled data.
        
        Args:
            sample_rate: The sample rate of the audio in Hz.
            num_channels: The number of audio channels.
            samples_per_channel: The number of samples per channel.
            
        Returns:
            AudioFrame: A new AudioFrame instance with zeroed data.
        """
        size = num_channels * samples_per_channel * ctypes.sizeof(ctypes.c_int16)
        data = bytearray(size)
        return AudioFrame(data, sample_rate, num_channels, samples_per_channel)
    
    @property
    def data(self) -> memoryview:
        """
        Returns a memory view of the audio data as 16-bit signed integers.
        
        Returns:
            memoryview: A memory view of the audio data (int16).
        """
        return memoryview(self._data).cast("B").cast("h")
    
    @property
    def sample_rate(self) -> int:
        """
        Returns the sample rate of the audio frame.
        
        Returns:
            int: The sample rate in Hz.
        """
        return self._sample_rate
    
    @property
    def num_channels(self) -> int:
        """
        Returns the number of channels in the audio frame.
        
        Returns:
            int: The number of audio channels (1 for mono, 2 for stereo).
        """
        return self._num_channels
    
    @property
    def samples_per_channel(self) -> int:
        """
        Returns the number of samples per channel.
        
        Returns:
            int: The number of samples per channel.
        """
        return self._samples_per_channel
    
    @property
    def duration(self) -> float:
        """
        Returns the duration of the audio frame in seconds.
        
        Returns:
            float: The duration in seconds.
        """
        return self._samples_per_channel / self._sample_rate
    
    def to_bytes(self) -> bytes:
        """
        Convert the audio frame data to raw bytes.
        
        Returns:
            bytes: The raw PCM audio data as bytes.
        """
        return bytes(memoryview(self._data).cast("B"))
    
    def to_wav_bytes(self) -> bytes:
        """
        Convert the audio frame data to a WAV-formatted byte stream.
        
        Returns:
            bytes: The audio data encoded in WAV format.
        """
        import wave
        import io
        
        with io.BytesIO() as wav_file:
            with wave.open(wav_file, "wb") as wav:
                wav.setnchannels(self._num_channels)
                wav.setsampwidth(2)  # 16-bit = 2 bytes
                wav.setframerate(self._sample_rate)
                wav.writeframes(self._data)
            
            return wav_file.getvalue()
    
    def __repr__(self) -> str:
        return (
            f"AudioFrame(sample_rate={self._sample_rate}, "
            f"num_channels={self._num_channels}, "
            f"samples_per_channel={self._samples_per_channel}, "
            f"duration={self.duration:.3f}s)"
        )
    
    def __len__(self) -> int:
        """Returns the total number of samples (all channels)."""
        return self._samples_per_channel * self._num_channels


def combine_audio_frames(buffer: AudioFrame | list[AudioFrame]) -> AudioFrame:
    """
    Combines one or more AudioFrame objects into a single AudioFrame.
    
    This function concatenates the audio data from multiple frames, ensuring that
    all frames have the same sample rate and number of channels. It efficiently
    merges the data by preallocating the necessary memory and copying the frame
    data without unnecessary reallocations.
    
    Args:
        buffer: A single AudioFrame or a list of AudioFrame objects to be combined.
        
    Returns:
        AudioFrame: A new AudioFrame containing the combined audio data.
        
    Raises:
        ValueError: If the buffer is empty.
        ValueError: If frames have differing sample rates.
        ValueError: If frames have differing numbers of channels.
        
    Example:
        >>> frame1 = AudioFrame(
        ...     data=b"\\x01\\x00\\x02\\x00",
        ...     sample_rate=16000,
        ...     num_channels=1,
        ...     samples_per_channel=2
        ... )
        >>> frame2 = AudioFrame(
        ...     data=b"\\x03\\x00\\x04\\x00",
        ...     sample_rate=16000,
        ...     num_channels=1,
        ...     samples_per_channel=2
        ... )
        >>> combined = combine_audio_frames([frame1, frame2])
        >>> combined.samples_per_channel
        4
        >>> combined.duration
        0.00025
    """
    # If single frame, return as-is
    if not isinstance(buffer, list):
        return buffer
    
    if not buffer:
        raise ValueError("buffer is empty")
    
    # Get properties from first frame
    sample_rate = buffer[0].sample_rate
    num_channels = buffer[0].num_channels
    
    # Calculate total size
    total_data_length = 0
    total_samples_per_channel = 0
    
    for frame in buffer:
        # Validate consistency
        if frame.sample_rate != sample_rate:
            raise ValueError(
                f"Sample rate mismatch: expected {sample_rate}, got {frame.sample_rate}"
            )
        
        if frame.num_channels != num_channels:
            raise ValueError(
                f"Channel count mismatch: expected {num_channels}, got {frame.num_channels}"
            )
        
        total_data_length += len(frame.data)
        total_samples_per_channel += frame.samples_per_channel
    
    # Allocate combined buffer
    data = bytearray(total_data_length * ctypes.sizeof(ctypes.c_int16))
    offset = 0
    
    # Copy all frame data
    for frame in buffer:
        frame_data = frame.data.cast("b")
        data[offset : offset + len(frame_data)] = frame_data
        offset += len(frame_data)
    
    return AudioFrame(
        data=data,
        sample_rate=sample_rate,
        num_channels=num_channels,
        samples_per_channel=total_samples_per_channel,
    )


class AudioByteStream:
    """
    A utility class for streaming audio data and converting it into AudioFrame objects.
    
    This class buffers incoming audio data and yields complete AudioFrame objects
    when enough samples are available.
    
    Example:
        >>> stream = AudioByteStream(sample_rate=16000, num_channels=1)
        >>> async for frame in stream:
        ...     # Process each 100ms frame
        ...     process_audio(frame)
    """
    
    def __init__(
        self,
        sample_rate: int,
        num_channels: int,
        samples_per_channel: int = 960,  # Default: 60ms at 16kHz
    ) -> None:
        """
        Initialize an AudioByteStream.
        
        Args:
            sample_rate: The sample rate in Hz.
            num_channels: The number of audio channels.
            samples_per_channel: The number of samples per channel per frame.
                Default is 960 samples (60ms at 16kHz).
        """
        self._sample_rate = sample_rate
        self._num_channels = num_channels
        self._samples_per_channel = samples_per_channel
        
        self._bytes_per_sample = num_channels * ctypes.sizeof(ctypes.c_int16)
        self._bytes_per_frame = samples_per_channel * self._bytes_per_sample
        
        self._buffer = bytearray()
    
    def write(self, data: Union[bytes, bytearray]) -> list[AudioFrame]:
        """
        Write audio data to the stream and return any complete frames.
        
        Args:
            data: Raw PCM audio data (int16).
            
        Returns:
            list[AudioFrame]: A list of complete AudioFrame objects.
        """
        self._buffer.extend(data)
        frames: list[AudioFrame] = []
        
        while len(self._buffer) >= self._bytes_per_frame:
            frame_data = self._buffer[: self._bytes_per_frame]
            self._buffer = self._buffer[self._bytes_per_frame :]
            
            frames.append(
                AudioFrame(
                    data=frame_data,
                    sample_rate=self._sample_rate,
                    num_channels=self._num_channels,
                    samples_per_channel=self._samples_per_channel,
                )
            )
        
        return frames
    
    def flush(self) -> AudioFrame | None:
        """
        Flush any remaining data in the buffer as an AudioFrame.
        
        Returns:
            AudioFrame | None: The remaining data as an AudioFrame, or None if empty.
        """
        if not self._buffer:
            return None
        
        # Calculate samples from remaining bytes
        remaining_samples = len(self._buffer) // self._bytes_per_sample
        
        if remaining_samples == 0:
            return None
        
        frame_data = bytes(self._buffer)
        self._buffer.clear()
        
        return AudioFrame(
            data=frame_data,
            sample_rate=self._sample_rate,
            num_channels=self._num_channels,
            samples_per_channel=remaining_samples,
        )
    
    @property
    def sample_rate(self) -> int:
        """The sample rate in Hz."""
        return self._sample_rate
    
    @property
    def num_channels(self) -> int:
        """The number of audio channels."""
        return self._num_channels
    
    @property
    def samples_per_channel(self) -> int:
        """The number of samples per channel per frame."""
        return self._samples_per_channel

