"""
OpenAI LLM Provider
"""
from __future__ import annotations
import httpx
import openai
import logging
from typing import Any, AsyncGenerator, Literal
from openai import AsyncStream
from openai.types import CompletionUsage
from openai.types.responses.response_stream_event import ResponseStreamEvent
from openai.types.responses.response_output_item_done_event import ResponseOutputItemDoneEvent
from openai.types.responses.response_completed_event import ResponseCompletedEvent
from openai.types.responses.response_output_message import ResponseOutputMessage
from openai.types.responses.response_output_text import ResponseOutputText
from openai.types.responses.response_output_refusal import ResponseOutputRefusal
from openai.types.responses.response_function_tool_call import ResponseFunctionToolCall
from core.utils.util import check_model_key
import core.llm.base as base
from ..base import ChatChunk, ChatDelta, CompletionUsage
from core.dialogue.context import ChatContext
from core.dialogue.items import FunctionCall



class LLM(base.LLM):
    """
    OpenAI LLM Provider
    
    Supports:
    - OpenAI official API
    - Compatible services (Groq, DeepSeek, etc.)
    """
    
    def __init__(self, config):
        self.model_name = config.get("model_name")
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url")
        
        # Timeout configuration
        self.timeout = config.get("timeout", 300)
        self.max_retries = config.get("max_retries", 0)

        self.max_output_tokens = config.get("max_output_tokens", 500)
        self.temperature = config.get("temperature", 0.7)
        self.top_p = config.get("top_p", 1.0)
        self.frequency_penalty = config.get("frequency_penalty", 0)

        # Validate API key
        model_key_msg = check_model_key("LLM", self.api_key)
        if model_key_msg:
            logging.warning(model_key_msg)

        # Create async client with optimized settings
        self.client = openai.AsyncClient(
            api_key=self.api_key,
            base_url=self.base_url,
            max_retries=self.max_retries,
            http_client=httpx.AsyncClient(
                timeout=self.timeout 
                if self.timeout else httpx.Timeout(connect=15.0, read=5.0, write=5.0, pool=5.0),
                follow_redirects=True,
                limits=httpx.Limits(
                    max_connections=50,
                    max_keepalive_connections=50,
                    keepalive_expiry=120,
                ),
            ),
        )
    
    @classmethod
    async def from_config(cls, config) -> LLM:
        """
        Create OpenAI LLM instance from configuration.
        
        Args:
            config: LLM configuration object with structure:
                - provider: "openai"
                - model:
                    - name: model name (e.g., "gpt-4")
                    - base_url: optional custom base URL
                - options: optional dict with:
                    - api_key: API key (or from env OPENAI_API_KEY)
                    - timeout: request timeout in seconds
                    - max_retries: maximum retry attempts
                    - max_output_tokens: maximum output tokens
                    - temperature: sampling temperature
                    - top_p: nucleus sampling parameter
                    - frequency_penalty: frequency penalty
        
        Returns:
            Initialized OpenAI LLM instance
        """
        import os
        
        options = config.options or {}
        
        # Build config dict for __init__
        llm_config = {
            "model_name": config.model.name,
            "base_url": config.model.base_url if config.model.base_url else None,
            "api_key": options.get("api_key") or os.environ.get("OPENAI_API_KEY"),
            "timeout": options.get("timeout", 300),
            "max_retries": options.get("max_retries", 0),
            "max_output_tokens": options.get("max_output_tokens", 500),
            "temperature": options.get("temperature", 0.7),
            "top_p": options.get("top_p", 1.0),
            "frequency_penalty": options.get("frequency_penalty", 0),
        }
        
        instance = cls(llm_config)
        
        logging.info(
            f"✓ OpenAI LLM loaded: model={config.model.name}, "
            f"base_url={llm_config['base_url']}"
        )
        
        return instance

    async def response_stream(
        self,
        chat_ctx: ChatContext,
        **kwargs: Any
    ) -> AsyncGenerator[ChatChunk, None]:
        """
        New streaming interface using standard protocol
        
        This method implements the new standard interface defined in LLMProviderBase.
        It uses:
        - ChatContext as input (standard dialogue protocol)
        - ChatChunk as output (standard streaming protocol)
        - OpenAI Responses API (modern response.create)
        
        Args:
            chat_ctx: Standard ChatContext with dialogue history
            **kwargs: Additional options:
                - max_output_tokens: Override max tokens
                - temperature: Override temperature
                - top_p: Override top_p
                - frequency_penalty: Override frequency penalty
        
        Yields:
            ChatChunk: Standardized streaming chunks with deltas and usage
        
        Example:
            async for chunk in provider.response_stream(chat_ctx):
                if chunk.delta and chunk.delta.content:
                    print(chunk.delta.content)
                if chunk.usage:
                    print(f"Tokens: {chunk.usage.total_tokens}")
        """
        try:
            # 1. Convert ChatContext to OpenAI format
            messages, _ = chat_ctx.to_provider_format(format="openai")
            
            logging.debug(
                f"Starting streaming with model={self.model_name}, "
                f"messages_count={len(messages)}"
            )
            
            # 2. Prepare request parameters
            max_output_tokens = kwargs.get("max_output_tokens", self.max_output_tokens)
            temperature = kwargs.get("temperature", self.temperature)
            top_p = kwargs.get("top_p", self.top_p)
            frequency_penalty = kwargs.get("frequency_penalty", self.frequency_penalty)
            
            # 3. Call OpenAI Responses API
            # TODO: system instruction needs to be added
            stream: AsyncStream[ResponseStreamEvent] = await self.client.responses.create(
                input=messages,
                model=self.model_name,
                stream=True,
                max_output_tokens=max_output_tokens,
                temperature=temperature,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
            )
            
            # 4. Parse stream and yield ChatChunk (focus on output_item.done + completed)
            async for event in stream:
                try:
                    chunk = self._parse_response_event(event)
                    if chunk:
                        yield chunk
                except (IndexError, AttributeError) as e:
                    logging.debug(f"Skipping malformed event: {e}")
                    continue
            
            logging.debug("Stream completed successfully")
            
        except openai.APIError as e:
            error_msg = f"OpenAI API error: {e.message if hasattr(e, 'message') else str(e)}"
            logging.error(error_msg)
            # Yield error chunk
            yield ChatChunk(
                delta=ChatDelta(
                    role="assistant",
                    content=f"API error: {error_msg}"
                )
            )
            
            
        except Exception as e:
            error_msg = f"Unexpected error: {type(e).__name__}: {str(e)}"
            logging.error(error_msg)
            yield ChatChunk(
                delta=ChatDelta(
                    role="assistant",
                    content=f"【服务异常: {str(e)}】"
                )
            )

    def _parse_response_event(
        self,
        event: ResponseStreamEvent,
    ) -> ChatChunk | None:
        """
        Parse OpenAI ResponseStreamEvent to standard ChatChunk
        
        Focus on finalized events per Responses API:
        - response.output_item.done → emits assistant message text or function_call
        - response.completed → emits usage
        Reasoning events are ignored.
        """
        # Finalized output item (message | function_call)
        if event.type == "response.output_item.done":
            item = event.item

            if item.type == "message":
                parts: list[str] = []
                for c in item.content:
                    if c.type == "output_text":
                        parts.append(c.text)
                    # Intentionally ignore refusal blocks here; they are not user-facing text
                if parts:
                    return ChatChunk(delta=ChatDelta(role="assistant", content=" ".join(parts)))
                return None

            if item.type == "function_call":
                call_id = item.call_id or (item.id or "")
                return ChatChunk(
                    delta=ChatDelta(
                        role="assistant",
                        tool_calls=[
                            FunctionCall(
                                id=call_id or item.name,
                                call_id=call_id or item.name,
                                name=item.name,
                                arguments=item.arguments,
                            )
                        ],
                    )
                )

            # Ignore other item types here
            return None

        # Completed with possible usage stats
        elif event.type == "response.completed":
            if event.response and event.response.usage:
                usage = event.response.usage
                return ChatChunk(
                    usage=CompletionUsage(
                        completion_tokens=usage.completion_tokens or 0,
                        prompt_tokens=usage.prompt_tokens or 0,
                        total_tokens=usage.total_tokens or 0,
                    )
                )

        # Ignore reasoning-related events
        elif event.type in (
            "response.reasoning_text.delta",
            "response.reasoning_text.done",
            "response.reasoning_summary_text.delta",
            "response.reasoning_summary_text.done",
            "response.reasoning_summary_part.added",
            "response.reasoning_summary_part.done",
        ):
            return None

        return None
