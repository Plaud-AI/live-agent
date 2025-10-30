"""
Groq STT Models

Defines the supported audio models for Groq Speech-to-Text.
"""

from typing import Literal

# Groq supported STT models
STTModels = Literal[
    "whisper-large-v3",
    "whisper-large-v3-turbo",
]

