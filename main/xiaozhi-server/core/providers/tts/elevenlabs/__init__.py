"""
ElevenLabs TTS Provider

ElevenLabs provides high-quality, emotionally rich text-to-speech with advanced
voice cloning and multi-language support.

Key Features:
- WebSocket-based streaming synthesis with multi-stream support
- Voice settings (stability, similarity_boost, style, speed)
- Word-level timestamps with alignment
- SSML parsing support
- Auto-mode for optimized latency
- Connection pooling for multiple concurrent streams

Usage:
    from core.providers.tts.elevenlabs import TTS
    
    tts = TTS(
        api_key="your-api-key",
        voice_id="default-voice-id",
        model="eleven_turbo_v2_5",
        sample_rate=22050,
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
    Voice,
    VoiceSettings,
)
from .tts import TTS

__all__ = [
    "TTS",
    "VoiceSettings",
    "Voice",
    "DEFAULT_VOICE_ID",
    "TTSEncoding",
    "TTSModels",
]

