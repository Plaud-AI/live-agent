from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ==================== Template Schemas ====================

class AgentTemplateResponse(BaseModel):
    """Agent template response"""
    template_id: str
    name: str
    avatar_url: Optional[str] = None
    description: Optional[str] = None
    voice_id: Optional[str] = None
    instruction: Optional[str] = None
    voice_opening: Optional[str] = None
    voice_closing: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# ==================== Agent Response Schemas ====================

class AgentResponse(BaseModel):
    """Agent response"""
    agent_id: str
    name: str
    avatar_url: Optional[str] = None
    description: Optional[str] = None
    voice_id: Optional[str] = None
    instruction: str
    voice_opening: Optional[str] = None
    voice_closing: Optional[str] = None
    wake_word: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class BindableAgentResponse(BaseModel):
    """Agent that can be bound to device (has wake_word)"""
    agent_id: str
    name: str
    avatar_url: Optional[str] = None
    wake_word: str  # Required for bindable agents
    
    class Config:
        from_attributes = True


class BindableAgentListResponse(BaseModel):
    """List of agents that can be bound to device"""
    agents: list[BindableAgentResponse]


class AgentWithLatestMessage(BaseModel):
    """Agent with latest message for list view"""
    agent_id: str
    name: str
    avatar_url: Optional[str] = None
    last_activity_time: datetime  # 最近活动时间 (消息时间 or agent创建时间)
    latest_message_text: Optional[str] = None  # 最新消息的文本内容


class AgentListResponse(BaseModel):
    """Agent list response with cursor-based pagination"""
    agents: list[AgentWithLatestMessage]
    next_cursor: Optional[str] = None
    has_more: bool = False


class VoiceConfig(BaseModel):
    """Voice configuration for TTS"""
    voice_id: str                    # Our voice_id (voice_{ulid}) or Fish discover ID
    reference_id: str                # Provider's voice ID (Fish Audio ID, MiniMax ID)
    provider: str = "fishspeech"     # TTS provider: fishspeech or minimax


class RecentMessage(BaseModel):
    """Simplified message for dialogue context loading"""
    role: int  # 1: user, 2: agent
    content: List[dict]  # [{"message_type": "text|audio|image", "message_content": "..."}]


class AgentConfigResponse(BaseModel):
    """Agent configuration for xiaozhi-server"""
    agent_id: str
    name: str
    voice: Optional[VoiceConfig] = None  # Voice configuration with provider info
    language: Optional[str] = None       # Voice language from Fish Audio
    instruction: str
    voice_opening: Optional[str] = None
    voice_closing: Optional[str] = None
    enable_greeting: bool = True         # Whether to play greeting (false if already chatted today)
    greeting: Optional[str] = None       # Greeting text (same as voice_opening, only set when enabled)
    recent_messages: Optional[List[RecentMessage]] = None  # Recent conversation history for context
    raw_voice_id: Optional[str] = Field(default=None, exclude=True)  # Internal use: raw voice_id before enrichment

