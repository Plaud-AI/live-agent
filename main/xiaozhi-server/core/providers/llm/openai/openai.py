import httpx
import openai
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
from config.logger import setup_logging
from core.utils.util import check_model_key
from core.providers.llm.base import LLMProviderBase, ChatChunk, ChatDelta, CompletionUsage as StandardCompletionUsage
from core.dialogue.context import ChatContext
from core.dialogue.items import FunctionCall

TAG = __name__
logger = setup_logging()


class LLMProvider(LLMProviderBase):
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
            logger.bind(tag=TAG).warning(model_key_msg)

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

    async def response(self, session_id, dialogue):
        """
        Generate streaming response from LLM using new Responses API
        
        Supports:
        - Streaming text generation
        - Thinking tag filtering (<think>...</think>)
        - Modern OpenAI Responses API
        
        Args:
            session_id: Session identifier
            dialogue: List of message dictionaries
        
        Yields:
            str: Generated text chunks
        """
        try:
            
            # Create streaming response
            # TODO: system instruction needs to be added
            stream: AsyncStream[ResponseStreamEvent] = await self.client.responses.create(
                input=dialogue,
                model=self.model_name,
                stream=True, # indicate streaming mode
                max_output_tokens=self.max_output_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                frequency_penalty=self.frequency_penalty,
            )

            is_active = True
            total_content = ""
            
            async for event in stream:
                try:
                    # Handle thinking tags (for reasoning models like o1)
                    # Filter out content between <think>...</think>
                    content = event.output
                    if "<think>" in content:
                        is_active = False
                        content = content.split("<think>")[0]
                    
                    if "</think>" in content:
                        is_active = True
                        content = content.split("</think>")[-1]
                    
                    # Yield active content
                    if is_active and content:
                        yield content
                        
                except (IndexError, AttributeError) as e:
                    logger.bind(tag=TAG).debug(f"Skipping malformed event: {e}")
                    continue
            
            logger.bind(tag=TAG).debug(
                f"Completion finished: total_length={len(total_content)}"
            )

        except openai.APIError as e:
            error_msg = f"OpenAI API error: {e.message if hasattr(e, 'message') else str(e)}"
            logger.bind(tag=TAG).error(error_msg)
            yield f"【API错误: {error_msg}】"
            
        except openai.APIConnectionError as e:
            error_msg = f"Connection error: {str(e)}"
            logger.bind(tag=TAG).error(error_msg)
            yield f"【连接错误: 无法连接到服务】"
            
        except openai.RateLimitError as e:
            error_msg = f"Rate limit exceeded: {str(e)}"
            logger.bind(tag=TAG).error(error_msg)
            yield f"【请求过于频繁，请稍后再试】"
            
        except Exception as e:
            error_msg = f"Unexpected error in response generation: {type(e).__name__}: {str(e)}"
            logger.bind(tag=TAG).error(error_msg)
            yield f"【服务异常: {str(e)}】"

    async def response_with_functions(self, session_id, dialogue, functions=None):
        """
        Generate streaming response with function/tool calling support
        
        Supports:
        - OpenAI function calling
        - Tool calls (newer API)
        - Token usage reporting
        - Modern async/await pattern
        
        Args:
            session_id: Session identifier
            dialogue: List of message dictionaries
            functions: List of tool/function definitions
        
        Yields:
            tuple: (content: str or None, tool_calls: list or None)
        """
        try:
            # Prepare request parameters
            request_params = {
                "model": self.model_name,
                "messages": dialogue,
                "stream": True,
            }
            
            # Add tools/functions if provided
            if functions:
                request_params["tools"] = functions
                
            logger.bind(tag=TAG).debug(
                f"Creating completion with functions: model={self.model_name}, "
                f"tools_count={len(functions) if functions else 0}"
            )
            
            # Create streaming response
            stream = await self.client.chat.completions.create(**request_params)

            async for chunk in stream:
                try:
                    # Handle token usage reporting
                    if hasattr(chunk, "usage") and isinstance(chunk.usage, CompletionUsage):
                        usage_info = chunk.usage
                        logger.bind(tag=TAG).info(
                            f"Token usage - Input: {getattr(usage_info, 'prompt_tokens', 'unknown')}, "
                            f"Output: {getattr(usage_info, 'completion_tokens', 'unknown')}, "
                            f"Total: {getattr(usage_info, 'total_tokens', 'unknown')}"
                        )
                        continue
                    
                    # Handle response choices
                    if not hasattr(chunk, "choices") or not chunk.choices:
                        continue
                    
                    delta = chunk.choices[0].delta
                    
                    # Extract content and tool calls
                    content = getattr(delta, "content", None)
                    tool_calls = getattr(delta, "tool_calls", None)
                    
                    # Yield the chunk
                    yield content, tool_calls
                    
                except (IndexError, AttributeError) as e:
                    logger.bind(tag=TAG).debug(f"Skipping malformed chunk: {e}")
                    continue

        except openai.APIError as e:
            error_msg = f"OpenAI API error: {e.message if hasattr(e, 'message') else str(e)}"
            logger.bind(tag=TAG).error(error_msg)
            yield f"【API错误: {error_msg}】", None
            
        except openai.APIConnectionError as e:
            error_msg = f"Connection error: {str(e)}"
            logger.bind(tag=TAG).error(error_msg)
            yield f"【连接错误: 无法连接到服务】", None
            
        except openai.RateLimitError as e:
            error_msg = f"Rate limit exceeded: {str(e)}"
            logger.bind(tag=TAG).error(error_msg)
            yield f"【请求过于频繁，请稍后再试】", None
            
        except Exception as e:
            error_msg = f"Unexpected error in function calling: {type(e).__name__}: {str(e)}"
            logger.bind(tag=TAG).error(error_msg)
            yield f"【服务异常: {str(e)}】", None

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
            
            logger.bind(tag=TAG).debug(
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
                    logger.bind(tag=TAG).debug(f"Skipping malformed event: {e}")
                    continue
            
            logger.bind(tag=TAG).debug("Stream completed successfully")
            
        except openai.APIError as e:
            error_msg = f"OpenAI API error: {e.message if hasattr(e, 'message') else str(e)}"
            logger.bind(tag=TAG).error(error_msg)
            # Yield error chunk
            yield ChatChunk(
                delta=ChatDelta(
                    role="assistant",
                    content=f"【API错误: {error_msg}】"
                )
            )
            
        except openai.APIConnectionError as e:
            error_msg = f"Connection error: {str(e)}"
            logger.bind(tag=TAG).error(error_msg)
            yield ChatChunk(
                delta=ChatDelta(
                    role="assistant",
                    content="【连接错误: 无法连接到服务】"
                )
            )
            
        except openai.RateLimitError as e:
            error_msg = f"Rate limit exceeded: {str(e)}"
            logger.bind(tag=TAG).error(error_msg)
            yield ChatChunk(
                delta=ChatDelta(
                    role="assistant",
                    content="【请求过于频繁，请稍后再试】"
                )
            )
            
        except Exception as e:
            error_msg = f"Unexpected error: {type(e).__name__}: {str(e)}"
            logger.bind(tag=TAG).error(error_msg)
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
                    usage=StandardCompletionUsage(
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
