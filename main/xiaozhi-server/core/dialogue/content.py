"""
Content types for chat messages

Supports text (as plain string), image, and audio content in messages.
"""

from dataclasses import dataclass
from typing import Literal, Union


@dataclass
class ImageContent:
    """Image content (URL or data URL)"""

    image: str  # URL or data:image/...;base64,...
    type: Literal["image"] = "image"
    detail: Literal["auto", "high", "low"] = "auto"  # For vision models
    mime_type: str | None = None


@dataclass
class AudioContent:
    """Audio content"""

    audio_data: bytes | str  # Raw bytes or base64 string
    type: Literal["audio"] = "audio"
    transcript: str | None = None
    format: str = "pcm"  # pcm, mp3, wav, etc.


# Union type for all content types
# Plain string for simple text messages, structured types for complex content
ChatContent = Union[str, ImageContent, AudioContent]

