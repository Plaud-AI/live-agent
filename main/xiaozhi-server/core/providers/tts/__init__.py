"""
TTS Providers Module

This module provides Text-to-Speech functionality through various providers.

Modern TTS Architecture (Phase 5):
- TTS: Base class for all TTS providers
- ChunkedStream: Non-streaming synthesis (full text at once)
- SynthesizeStream: Streaming synthesis (incremental text input)
- StreamAdapter: Wrap non-streaming TTS to provide streaming interface
- AudioEmitter: Audio frame management and emission
- SentenceStreamPacer: Smart text pacing based on audio buffer

Available Providers:
- CartesiaTTS: High-quality, low-latency streaming TTS with voice cloning
- ElevenlabsTTS: Emotionally rich TTS with advanced voice controls

Basic Data Structures:
- SynthesizedAudio: Output audio frame with metadata
- TTSCapabilities: TTS provider capabilities descriptor

Legacy:
- TTSProviderBase: Legacy TTS provider base class (for backward compatibility)
"""

from .base import (
    # Modern TTS classes
    TTS,
    ChunkedStream,
    SynthesizeStream,
    # Data structures
    SynthesizedAudio,
    TTSCapabilities,
    # Legacy
    TTSProviderBase,
)

from .stream_adapter import StreamAdapter

from .emitter import AudioEmitter

from .pacer import (
    SentenceStreamPacer,
    StreamPacerWrapper,
)

from .cartesia import TTS as CartesiaTTS
from .elevenlabs import TTS as ElevenlabsTTS

__all__ = [
    # Modern TTS base classes
    "TTS",
    "ChunkedStream",
    "SynthesizeStream",
    # Streaming utilities
    "StreamAdapter",
    "AudioEmitter",
    "SentenceStreamPacer",
    "StreamPacerWrapper",
    # Data structures
    "SynthesizedAudio",
    "TTSCapabilities",
    # Modern providers
    "CartesiaTTS",
    "ElevenlabsTTS",
    # Legacy (backward compatibility)
    "TTSProviderBase",
]

