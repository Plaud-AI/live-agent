import httpx
import openai
from openai.types import CompletionUsage
from openai.types.responses import Response
from openai.types.responses import (
    ResponseOutputItemAddedEvent,
    ResponseOutputItemDoneEvent,
    ResponseTextDeltaEvent, 
    ResponseFunctionCallArgumentsDeltaEvent, 
    ResponseFunctionCallArgumentsDoneEvent
)
from config.logger import setup_logging
from core.utils.util import check_model_key
from core.providers.llm.base import LLMProviderBase
from types import SimpleNamespace
import time
from typing import List, Optional, Dict, Any

TAG = __name__
logger = setup_logging()


class LLMProvider(LLMProviderBase):
    def __init__(self, config):
        self.model_name = config.get("model_name")
        self.api_key = config.get("api_key")
        if "base_url" in config:
            self.base_url = config.get("base_url")
        else:
            self.base_url = config.get("url")
        # Default timeout for normal requests
        timeout = config.get("timeout", 10)
        self.timeout = int(timeout) if timeout else 10

        param_defaults = {
            "max_tokens": (1000, int),
            "temperature": (0.7, lambda x: round(float(x), 1)),
            "top_p": (1.0, lambda x: round(float(x), 1)),
            "frequency_penalty": (0, lambda x: round(float(x), 1)),
        }

        reasoning_effort = config.get("reasoning_effort", "none")
        self._reasoning_effort = reasoning_effort

        self._provider = config.get("provider", None)

        # Client-side fallback configuration
        self.fallback_models: List[Dict[str, str]] = config.get("fallback_models", [])
        self.allow_fallbacks = True if len(self.fallback_models) > 0 else False
        self.fallback_timeout = int(config.get("fallback_timeout", 3))

        for param, (default, converter) in param_defaults.items():
            value = config.get(param)
            try:
                setattr(
                    self,
                    param,
                    converter(value) if value not in (None, "") else default,
                )
            except (ValueError, TypeError):
                setattr(self, param, default)


        if self.fallback_models:
            logger.bind(tag=TAG).info(
                f"Fallback models configured: {[m.get('model') for m in self.fallback_models]}, "
                f"timeout={self.fallback_timeout}s"
            )

        model_key_msg = check_model_key("LLM", self.api_key)
        if model_key_msg:
            logger.bind(tag=TAG).error(model_key_msg)
        self.client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=httpx.Timeout(self.timeout))


    def _build_provider_extra_body(self, provider: Optional[str]) -> Optional[Dict[str, Any]]:
        """Build extra_body with provider config for OpenRouter."""
        if provider:
            return {
                "provider": {
                    "order": [provider],
                    "allow_fallbacks": False
                }
            }
        return None

    def prewarm(self):
        self.client.responses.create(
            model=self.model_name,
            input="test",
            stream=True,
            max_output_tokens=1,
            temperature=0.0,
            top_p=0.0,
            reasoning={
                "effort": self._reasoning_effort if self._reasoning_effort else "none"
            },
            extra_body=self._build_provider_extra_body(self._provider)
        )

    def response(self, session_id, dialogue, **kwargs):
        # Build model list: primary model first, then fallback models
        models = [(self.model_name, self._provider)]
        for m in self.fallback_models:
            models.append((m.get("model"), m.get("provider")))
        
        last_error = None
        for idx, (model_name, provider) in enumerate(models):
            is_fallback = idx > 0
            if is_fallback:
                logger.bind(tag=TAG).info(f"[Fallback] Trying model {idx + 1}/{len(models)}: {model_name}")
            
            start_time = time.time()
            try:
                responses = self.client.responses.create(
                    model=model_name,
                    input=dialogue,
                    stream=True,
                    max_output_tokens=kwargs.get("max_tokens", self.max_tokens),
                    temperature=kwargs.get("temperature", self.temperature),
                    top_p=kwargs.get("top_p", self.top_p),
                    reasoning={
                        "effort": self._reasoning_effort if self._reasoning_effort else "none"
                    },
                    extra_body=self._build_provider_extra_body(provider),
                    timeout=self.fallback_timeout if self.allow_fallbacks else None
                )

                first_chunk = True
                for chunk in responses:
                    if isinstance(chunk, ResponseTextDeltaEvent):
                        if first_chunk and is_fallback:
                            elapsed = (time.time() - start_time) * 1000
                            logger.bind(tag=TAG).info(f"[Fallback] Model {model_name} first chunk in {elapsed:.0f}ms")
                            first_chunk = False
                        yield chunk.delta
                return

            except httpx.TimeoutException as e:
                elapsed = (time.time() - start_time) * 1000
                prefix = "[Fallback] " if is_fallback else ""
                logger.bind(tag=TAG).warning(f"{prefix}Model {model_name} timeout after {elapsed:.0f}ms, trying next...")
                last_error = e
                
            except Exception as e:
                error_msg = repr(e) if e else "unknown error"
                if self.allow_fallbacks:
                    prefix = "[Fallback] " if is_fallback else ""
                    logger.bind(tag=TAG).warning(f"{prefix}Model {model_name} failed: {error_msg}, trying next...")
                else:
                    logger.bind(tag=TAG).error(f"Error in response generation: {error_msg}")
                last_error = e

        if self.allow_fallbacks:
            logger.bind(tag=TAG).error(f"All {len(models)} models failed. Last error: {last_error}")

    def response_with_functions(self, session_id, dialogue, functions=None):
        tools = self._build_tools(functions)
        
        # Build model list: primary model first, then fallback models
        models = [(self.model_name, self._provider)]
        for m in self.fallback_models:
            models.append((m.get("model"), m.get("provider")))
        
        last_error = None
        for idx, (model_name, provider) in enumerate(models):
            is_fallback = idx > 0
            if is_fallback:
                logger.bind(tag=TAG).info(f"[Fallback] Trying model {idx + 1}/{len(models)}: {model_name}")
            
            start_time = time.time()
            try:
                request_params = {
                    "model": model_name,
                    "input": dialogue,
                    "stream": True,
                    "max_output_tokens": self.max_tokens,
                    "temperature": self.temperature,
                    "top_p": self.top_p,
                    "reasoning": {
                        "effort": self._reasoning_effort if self._reasoning_effort else "none"
                    },
                    "extra_body": self._build_provider_extra_body(provider),
                    "timeout": self.fallback_timeout if self.allow_fallbacks else None
                }
                if tools:
                    request_params["tools"] = tools
                
                stream = self.client.responses.create(**request_params)

                first_chunk = True
                for chunk in stream:
                    if first_chunk and is_fallback:
                        elapsed = (time.time() - start_time) * 1000
                        logger.bind(tag=TAG).info(f"[Fallback] Model {model_name} first chunk in {elapsed:.0f}ms")
                        first_chunk = False
                    yield from self._process_function_chunk(chunk)
                return

            except httpx.TimeoutException as e:
                elapsed = (time.time() - start_time) * 1000
                prefix = "[Fallback] " if is_fallback else ""
                logger.bind(tag=TAG).warning(f"{prefix}Model {model_name} timeout after {elapsed:.0f}ms, trying next...")
                last_error = e
                
            except Exception as e:
                error_msg = repr(e) if e else "unknown error"
                if self.allow_fallbacks:
                    prefix = "[Fallback] " if is_fallback else ""
                    logger.bind(tag=TAG).warning(f"{prefix}Model {model_name} failed: {error_msg}, trying next...")
                else:
                    logger.bind(tag=TAG).error(f"Error in function call streaming: {error_msg}")
                last_error = e

        if self.allow_fallbacks:
            logger.bind(tag=TAG).error(f"All {len(models)} models failed. Last error: {last_error}")
        yield "LLM service error", None

    def _build_tools(self, functions):
        """Build tools list from functions."""
        if not functions:
            return None
        
        tools = []
        for f in functions:
            if f.get("type") == "function" and "function" in f:
                func = f["function"]
                tools.append({
                    "type": "function",
                    "name": func["name"],
                    "description": func.get("description", ""),
                    "parameters": func.get("parameters", {}),
                })
            else:
                tool = {k: v for k, v in f.items() if k != "strict"}
                tools.append(tool)
        return tools

    def _process_function_chunk(self, chunk):
        """Process a single chunk from function call stream."""
        if isinstance(chunk, ResponseOutputItemAddedEvent):
            if chunk.item.type == "function_call":
                yield None, [SimpleNamespace(
                    id=chunk.item.call_id,
                    type="function",
                    function=SimpleNamespace(
                        name=chunk.item.name,
                    ),
                )]
        elif isinstance(chunk, ResponseFunctionCallArgumentsDeltaEvent):
            yield None, [SimpleNamespace(
                function=SimpleNamespace(
                    arguments=chunk.item.arguments,
                ),
            )]
        elif isinstance(chunk, ResponseTextDeltaEvent):
            yield chunk.delta, None
