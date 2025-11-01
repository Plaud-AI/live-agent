"""
LLM Provider base class and streaming output

This module defines:
- ChatDelta: Incremental content delta from LLM (similar to Livekit's ChoiceDelta)
- ChatChunk: Unified streaming chunk format (similar to Livekit's ChatChunk)
- CompletionUsage: Token usage statistics
- LLMProviderBase: Base class that all LLM providers must inherit from
"""

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator

from core.dialogue.context import ChatContext
from core.dialogue.items import FunctionCall


@dataclass
class ChatDelta:
    """
    Incremental content delta from LLM stream
    
    Similar to Livekit's ChoiceDelta - represents a single delta in the stream.
    Can contain multiple types of information simultaneously.
    """

    # Role (usually only in first chunk)
    role: str | None = None

    # Text content delta
    content: str | None = None

    # Tool call deltas (can be multiple in one chunk)
    tool_calls: list[FunctionCall] = field(default_factory=list)


@dataclass
class CompletionUsage:
    """Token usage statistics"""

    completion_tokens: int = 0
    prompt_tokens: int = 0
    total_tokens: int = 0


@dataclass
class ChatChunk:
    """
    LLM streaming output chunk
    
    Similar to Livekit's ChatChunk - represents a single chunk of LLM output.
    Simple and intuitive - just access the fields you need, no type checking required.
    """

    # Chunk ID
    id: str = field(default_factory=lambda: f"chunk_{uuid.uuid4().hex[:16]}")

    # Content delta (if present)
    delta: ChatDelta | None = None

    # Token usage (usually only in last chunk)
    usage: CompletionUsage | None = None

    def __repr__(self) -> str:
        parts = [f"ChatChunk(id='{self.id[:12]}...'"]
        if self.delta:
            if self.delta.content:
                preview = self.delta.content[:30] + "..." if len(self.delta.content) > 30 else self.delta.content
                parts.append(f"content='{preview}'")
            if self.delta.tool_calls:
                parts.append(f"tool_calls={len(self.delta.tool_calls)}")
        if self.usage:
            parts.append(f"usage={self.usage.total_tokens}")
        return ", ".join(parts) + ")"


class LLM(ABC):
    """
    Base class for all LLM providers
    
    Providers must implement:
    
    response_stream(chat_ctx) -> AsyncGenerator[ChatChunk, None]
       - Recommended for new providers
       - Supports text, tool calls, and usage information
    
    Each provider decides how to implement these methods. No automatic bridging.
    """

    def response_stream(
        self,
        chat_ctx: ChatContext,
        **kwargs: Any
    ) -> AsyncGenerator[ChatChunk, None]:
        """
        New streaming response interface (OPTIONAL but RECOMMENDED)
        
        Args:
            chat_ctx: Standard ChatContext with dialogue history
            **kwargs: Provider-specific options
        
        Yields:
            ChatChunk: Standardized streaming chunks with deltas and usage
        
        Note:
            New providers should implement this method.
            If not implemented, raises NotImplementedError.
        """
        raise NotImplementedError("Provider does not support response_stream()")


# Factory function for creating LLM instances from configuration

async def create_from_config(config) -> LLM:
    """
    Factory function to create LLM instance from configuration.
    
    Args:
        config: LLM configuration object (from config.components.llm)
        
    Returns:
        Initialized LLM instance
        
    Raises:
        ValueError: If the specified provider is not supported
        
    Example:
        config = load_config("config.yaml")
        llm = await create_from_config(config.components.llm)
    """
    import logging
    
    provider = config.provider.lower()
    logging.info(f"Creating LLM: provider={provider}, model={config.model.name}")
    
    if provider == "groq":
        from core.llm.groq import LLM as GroqLLM
        return await GroqLLM.from_config(config)
    elif provider == "openai":
        from core.llm.openai import LLM as OpenAILLM
        return await OpenAILLM.from_config(config)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
