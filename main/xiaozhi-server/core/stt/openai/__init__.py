"""
OpenAI STT Provider

OpenAI Speech-to-Text implementation.
"""

from .models import STTModels
from .stt import STT

__all__ = ["STT", "STTModels"]

