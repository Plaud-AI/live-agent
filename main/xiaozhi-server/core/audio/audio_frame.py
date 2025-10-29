"""
Audio Frame Data Structure

Provides a unified audio frame representation for the TTS pipeline.
Based on LiveKit's rtc.AudioFrame design.
"""

from dataclasses import dataclass
from typing import Union
import ctypes


@dataclass
class AudioFrame:
    """
    Represents a single audio frame with PCM audio data.
    """

    def __init__(
        self,
        audio_data: Union[bytes, bytearray, memoryview],
        sample_rate: int,
        num_channels: int,
        samples_per_channel: int,
    ):
        """
        Initialize an AudioFrame instance.

        Args:
            audio_data (Union[bytes, bytearray, memoryview]): The raw audio data, which must be at least
                `num_channels * samples_per_channel * sizeof(int16)` bytes long.
            sample_rate (int): The sample rate of the audio in Hz.
            num_channels (int): The number of audio channels (e.g., 1 for mono, 2 for stereo).
            samples_per_channel (int): The number of samples per channel.

        Raises:
            ValueError: If the length of `data` is smaller than the required size.
        """
        data = memoryview(audio_data).cast('B')
        if len(data) < num_channels * samples_per_channel * ctypes.sizeof(ctypes.c_int16):
            raise ValueError(
                "data length must be >= num_channels * samples_per_channel * sizeof(int16)"
            )
        if len(data) % ctypes.sizeof(ctypes.c_int16) != 0:
            # can happen if data is bigger than needed
            raise ValueError("data length must be a multiple of sizeof(int16)")

        n = len(data) // ctypes.sizeof(ctypes.c_int16)
        self._data = (ctypes.c_int16 * n).from_buffer_copy(data)

        self._sample_rate = sample_rate
        self._num_channels = num_channels
        self._samples_per_channel = samples_per_channel
    
    @property
    def data(self) -> memoryview:
        """Return the audio data as a memoryview"""
        return memoryview(self._data).cast('B').cast('h')
    
    @property
    def sample_rate(self) -> int:
        """
        Returns the sample rate of the audio frame.

        Returns:
            int: The sample rate in Hz.
        """
        return self._sample_rate
    
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
        """Calculate and return the duration of this audio frame in seconds"""
        return self.samples_per_channel / self.sample_rate
    
    def to_wav_bytes(self) -> bytes:
        """
        Convert the audio frame to WAV format bytes.
        
        Returns:
            bytes: WAV format audio data
        """
        import wave
        import io

        with io.BytesIO() as wav_file:
            with wave.open(wav_file, "wb") as wav:
                wav.setnchannels(self.num_channels)
                wav.setsampwidth(2)
                wav.setframerate(self.sample_rate)
                wav.writeframes(self._data)

            return wav_file.getvalue()
    
    @staticmethod
    def combine_frames(frames: list['AudioFrame']) -> 'AudioFrame':
        """
        Combine multiple audio frames into a single frame.
        
        All frames must have the same sample_rate and num_channels.
        
        Args:
            frames: List of AudioFrame objects to combine
            
        Returns:
            AudioFrame: A single combined audio frame
            
        Raises:
            ValueError: If frames have incompatible parameters
        """
        if not frames:
            raise ValueError("Cannot combine empty list of frames")
        
        # Validate all frames have the same parameters
        first_frame = frames[0]
        for frame in frames[1:]:
            if frame.sample_rate != first_frame.sample_rate:
                raise ValueError(
                    f"Incompatible sample rates: {frame.sample_rate} != {first_frame.sample_rate}"
                )
            if frame.num_channels != first_frame.num_channels:
                raise ValueError(
                    f"Incompatible channel counts: {frame.num_channels} != {first_frame.num_channels}"
                )
        
        # Combine audio data
        combined_data = b''.join(frame.data for frame in frames)
        total_samples = sum(frame.samples_per_channel for frame in frames)
        
        return AudioFrame(
            data=combined_data,
            sample_rate=first_frame.sample_rate,
            num_channels=first_frame.num_channels,
            samples_per_channel=total_samples,
        )

