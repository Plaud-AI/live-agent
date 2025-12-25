from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

# Re-export enums from repository for API usage
from repositories.voice import VoiceCategory, VoiceProvider, GenderTag, AgeTag


# ==================== Request Schemas ====================

class VoiceCloneRequest(BaseModel):
    """Voice clone request"""
    name: str = Field(..., min_length=1, max_length=100)
    reference_text: Optional[str] = None
    tags: Optional[List[str]] = None


class VoiceUpdateRequest(BaseModel):
    """Voice update request"""
    name: str = Field(None, min_length=1, max_length=100, description="Voice name")
    desc: str = Field(None, max_length=500, description="Voice description")


class VoiceAddRequest(BaseModel):
    """Voice add request"""
    name: str = Field(..., min_length=1, max_length=100, description="Voice name")
    desc: str = Field(..., max_length=500, description="Voice description")
    sample_url: Optional[str] = Field(None, description="URL of stored audio sample (for cloned voices)")
    sample_text: Optional[str] = Field(None, description="Transcription text (for cloned voices)")


# ==================== Response Schemas ====================

class AudioSample(BaseModel):
    """Audio sample"""
    text: Optional[str] = None
    audio: Optional[str] = None


class VoiceTags(BaseModel):
    """Voice tags for filtering and display"""
    gender: Optional[str] = None      # male / female
    age: Optional[str] = None         # youth / young_adult / adult / middle_aged / senior
    language: Optional[str] = None    # en / zh / ja / etc.
    style: Optional[str] = None       # audiobook / informative / social_media / etc.
    accent: Optional[str] = None      # en-british / en-us / etc.
    description: Optional[str] = None # Brief voice description


class LiveAgentVoice(BaseModel):
    """Voice Entity for Live Agent"""
    voice_id: str
    name: str
    desc: Optional[str] = None

    samples: Optional[List[AudioSample]] = None

    created_at: Optional[datetime] = None


class VoiceLibraryItem(BaseModel):
    """Voice Library item with tags for display"""
    voice_id: str
    name: str
    desc: Optional[str] = None
    
    # Provider info
    provider: str = VoiceProvider.FISHSPEECH.value
    
    # Tags for filtering and display
    tags: Optional[VoiceTags] = None
    
    # Audio sample
    sample_url: Optional[str] = None
    sample_text: Optional[str] = None
    
    created_at: Optional[datetime] = None


class VoiceLibraryResponse(BaseModel):
    """Voice library response with cursor-based pagination"""
    voices: List[VoiceLibraryItem]
    next_cursor: Optional[str] = None
    has_more: bool = False


class FishAudioVoiceResponse(BaseModel):
    """Fish Audio voice response (for discover tab)"""
    voice_id: str
    name: str
    tags: Optional[List[str]] = None
    preview_url: Optional[str] = None
    author_id: Optional[str] = None
    author_name: Optional[str] = None
    like_count: Optional[int] = None
    task_count: Optional[int] = None


class DiscoverVoiceResponse(BaseModel):
    """Voice list response"""
    voices: List[LiveAgentVoice]
    has_more: bool


class MyVoiceResponse(BaseModel):
    """My voice response with cursor-based pagination"""
    voices: List[LiveAgentVoice]
    next_cursor: Optional[str] = None
    has_more: bool = False


class VoiceCloneStatusResponse(BaseModel):
    """Voice clone status response"""
    voice_id: str
    status: str  # processing | completed | failed
    error_message: Optional[str] = None
    voice: Optional[LiveAgentVoice] = None
    
    class Config:
        from_attributes = True
