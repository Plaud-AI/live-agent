"""
OpenAI ASR Provider

OpenAI Speech-to-Text implementation.
"""

from .models import STTModels
from .stt import ASR

__all__ = ["ASR", "STTModels"]

