"""
Cartesia TTS Models and Constants

Defines available models, voices, and encoding formats for Cartesia TTS.
"""

from typing import Literal

# TTS Models
TTSModels = Literal[
    "sonic-2",
    "sonic-3",
]

# Audio Encoding Formats
TTSEncoding = Literal[
    "pcm_s16le",  # 16-bit PCM (recommended for real-time)
]

# Default voice ID (British Lady)
DEFAULT_VOICE_ID = "a0e99841-438c-4a64-b679-ae501e7d6091"

# API Endpoints
API_BASE_URL = "https://api.cartesia.ai"
API_VERSION = "2025-04-16"

