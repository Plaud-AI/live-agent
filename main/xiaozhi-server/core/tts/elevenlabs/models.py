"""
ElevenLabs TTS Models and Constants

Defines available models, voices, encoding formats, and voice settings.
"""

from dataclasses import dataclass
from typing import Literal

# TTS Models
TTSModels = Literal[
    "eleven_multilingual_v2",
    "eleven_turbo_v2_5",
    "eleven_flash_v2_5",
    "eleven_v3",
]

# Audio Encoding Formats
TTSEncoding = Literal[
    "mp3_22050_32",   # MP3 at 22.05kHz, 32kbps (default, fast)
    "mp3_44100_32",   # MP3 at 44.1kHz, 32kbps
    "mp3_44100_64",   # MP3 at 44.1kHz, 64kbps
    "mp3_44100_96",   # MP3 at 44.1kHz, 96kbps
    "mp3_44100_128",  # MP3 at 44.1kHz, 128kbps (high quality)
    "mp3_44100_192",  # MP3 at 44.1kHz, 192kbps (highest quality)
    "pcm_16000",      # PCM at 16kHz
    "pcm_22050",      # PCM at 22.05kHz
    "pcm_24000",      # PCM at 24kHz
    "pcm_44100",      # PCM at 44.1kHz (high quality)
    "ulaw_8000",      # μ-law at 8kHz (telephony)
]


@dataclass
class VoiceSettings:
    """
    Voice settings for fine-tuning synthesis quality.
    
    Attributes:
        stability: Stability of the voice (0.0-1.0). Higher = more consistent.
        similarity_boost: Similarity to original voice (0.0-1.0). Higher = closer match.
        style: Style exaggeration (0.0-1.0). Optional.
        speed: Speaking speed (0.8-1.2). Optional. 1.0 = normal speed.
        use_speaker_boost: Whether to use speaker boost for better quality. Optional.
    """
    stability: float
    similarity_boost: float
    style: float | None = None
    speed: float | None = None
    use_speaker_boost: bool | None = None


@dataclass
class Voice:
    """
    Voice information from ElevenLabs API.
    
    Attributes:
        id: Voice ID
        name: Voice name
        category: Voice category (e.g., "premade", "cloned")
    """
    id: str
    name: str
    category: str


# Default voice ID (Rachel - Natural female voice)
DEFAULT_VOICE_ID = "bIHbv24MWmeRgasZH58o"

# API Endpoints
API_BASE_URL = "https://api.elevenlabs.io/v1"
WS_INACTIVITY_TIMEOUT = 180  # seconds

