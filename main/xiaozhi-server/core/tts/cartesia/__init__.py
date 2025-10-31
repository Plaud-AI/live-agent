"""
Cartesia TTS Provider

Cartesia provides high-quality, low-latency text-to-speech with voice cloning
and emotion control capabilities.

Key Features:
- WebSocket-based streaming synthesis
- Voice embeddings support
- Speed and emotion controls
- Word-level timestamps (optional)
- Context-based cancellation

Usage:
    from core.providers.tts.cartesia import TTS
    
    tts = TTS(
        api_key="your-api-key",
        model="sonic-3",
        voice="default-voice-id",
        sample_rate=24000,
    )
    
    # Streaming synthesis
    stream = tts.stream()
    stream.push_text("Hello ")
    stream.push_text("world!")
    stream.end_input()
    
    async for audio in stream:
        # Process audio frames
        pass
"""

from .models import (
    DEFAULT_VOICE_ID,
    TTSEncoding,
    TTSModels,
)
from .tts import TTS

__all__ = [
    "TTS",
    "DEFAULT_VOICE_ID",
    "TTSEncoding",
    "TTSModels",
]

