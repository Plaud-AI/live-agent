"""
OpenAI format converter

Converts ChatContext to OpenAI-compatible API format.
Only handles INPUT conversion (ChatContext → OpenAI messages).
Output parsing (OpenAI response → ChatChunk) is done in the provider itself.
"""

from typing import Any, Literal

from ..content import ImageContent, AudioContent
from ..items import ChatMessage, FunctionCallOutput
from .utils import group_tool_calls


def to_chat_ctx(
    items: list,
    **kwargs: Any
) -> tuple[list[dict[str, Any]], None]:
    """
    Convert ChatContext items to OpenAI message format
    
    Args:
        items: List of ChatItem objects from ChatContext
        **kwargs: Reserved for future options
    
    Returns:
        tuple: (messages, None)
            - messages: List of OpenAI-format messages
            - None: OpenAI doesn't need extra data (unlike Anthropic)
    
    Example:
        Input ChatContext:
        - ChatMessage(role="user", content=["Hello"])
        - ChatMessage(role="assistant", content=["Hi"])
        - FunctionCall(name="get_weather", arguments='{"city": "Beijing"}')
        - FunctionCallOutput(output="Sunny, 25°C")
        
        Output:
        [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi", "tool_calls": [...]},
            {"role": "tool", "tool_call_id": "...", "content": "Sunny, 25°C"}
        ]
    """
    item_groups = group_tool_calls(items)
    messages: list[dict[str, Any]] = []
    
    for group in item_groups:
        # Skip empty groups
        if not group.message and not group.tool_calls and not group.tool_outputs:
            continue
        
        # Convert message (or create empty assistant message for tool calls)
        if group.message:
            msg = _to_openai_message(group.message)
        else:
            # Tool calls without preceding message - use empty assistant message
            msg = {"role": "assistant", "content": ""}
        
        # Add tool calls to message
        if group.tool_calls:
            tool_calls = [
                {
                    "id": call.call_id,
                    "type": "function",
                    "function": {
                        "name": call.name,
                        "arguments": call.arguments
                    }
                }
                for call in group.tool_calls
            ]
            msg["tool_calls"] = tool_calls
        
        messages.append(msg)
        
        # Add tool outputs as separate "tool" role messages
        for output in group.tool_outputs:
            messages.append(_to_openai_tool_output(output))
    
    return messages, None


def _to_openai_message(msg: ChatMessage) -> dict[str, Any]:
    """
    Convert ChatMessage to OpenAI message format
    
    Handles:
    - Text-only messages (string format)
    - Mixed content messages (list format with text + images)
    """
    list_content: list[dict[str, Any]] = []
    text_content = ""
    
    # Process all content items
    for content in msg.content:
        if isinstance(content, str):
            # Plain text
            if text_content:
                text_content += "\n"
            text_content += content
        
        elif isinstance(content, ImageContent):
            # Image content (for vision models)
            list_content.append(_to_openai_image(content))
        
        elif isinstance(content, AudioContent):
            # Audio content (for future multimodal support)
            # Currently just extract transcript if available
            if content.transcript:
                if text_content:
                    text_content += "\n"
                text_content += content.transcript
    
    # OpenAI prefers string for text-only content (better compatibility)
    if not list_content:
        return {"role": msg.role, "content": text_content}
    
    # Mixed content (text + images) - use list format
    if text_content:
        list_content.append({"type": "text", "text": text_content})
    
    return {"role": msg.role, "content": list_content}


def _to_openai_tool_output(output: FunctionCallOutput) -> dict[str, Any]:
    """
    Convert FunctionCallOutput to OpenAI tool message
    
    OpenAI expects tool outputs with role="tool" and tool_call_id.
    """
    return {
        "role": "tool",
        "tool_call_id": output.call_id,
        "content": output.output
    }


def _to_openai_image(image: ImageContent) -> dict[str, Any]:
    """
    Convert ImageContent to OpenAI vision format
    
    Supports:
    - HTTP/HTTPS URLs
    - Data URLs (data:image/...;base64,...)
    - Raw base64 strings
    """
    image_url = image.image
    
    # HTTP/HTTPS URL - use directly
    if image_url.startswith("http://") or image_url.startswith("https://"):
        return {
            "type": "image_url",
            "image_url": {
                "url": image_url,
                "detail": image.detail
            }
        }
    
    # Data URL - use directly
    if image_url.startswith("data:"):
        return {
            "type": "image_url",
            "image_url": {
                "url": image_url,
                "detail": image.detail
            }
        }
    
    # Raw base64 string - wrap in data URL
    mime_type = image.mime_type or "image/png"
    return {
        "type": "image_url",
        "image_url": {
            "url": f"data:{mime_type};base64,{image_url}",
            "detail": image.detail
        }
    }

