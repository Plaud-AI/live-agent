"""
Utility functions for provider format conversion
"""

from dataclasses import dataclass, field

from ..items import ChatMessage, FunctionCall, FunctionCallOutput


@dataclass
class ItemGroup:
    """
    Group of related chat items
    
    Groups a message with its associated tool calls and outputs.
    This matches the structure expected by most LLM providers.
    """
    
    message: ChatMessage | None = None
    tool_calls: list[FunctionCall] = field(default_factory=list)
    tool_outputs: list[FunctionCallOutput] = field(default_factory=list)


def group_tool_calls(items: list) -> list[ItemGroup]:
    """
    Group chat items by message + associated tool calls/outputs
    
    This ensures tool calls and outputs are properly associated with
    their parent messages, which is required by most provider APIs.
    
    Args:
        items: List of ChatItem objects
    
    Returns:
        List of ItemGroup objects
    
    Example:
        Input:
        - Message(role="user", content="What's the weather?")
        - Message(role="assistant", content="")
        - FunctionCall(name="get_weather", ...)
        - FunctionCallOutput(output="Sunny, 25°C")
        - Message(role="assistant", content="It's sunny...")
        
        Output:
        - Group(message=user_msg)
        - Group(message=assistant_msg, tool_calls=[call], tool_outputs=[output])
        - Group(message=assistant_response)
    """
    groups: list[ItemGroup] = []
    current_group: ItemGroup | None = None
    
    for item in items:
        if item.type == "message":
            # Start new group with message
            if current_group:
                groups.append(current_group)
            current_group = ItemGroup(message=item)
        
        elif item.type == "function_call":
            # Add tool call to current group
            if not current_group:
                # Tool call without message - create empty group
                current_group = ItemGroup()
            current_group.tool_calls.append(item)
        
        elif item.type == "function_call_output":
            # Add tool output to current group
            if not current_group:
                current_group = ItemGroup()
            current_group.tool_outputs.append(item)
    
    # Don't forget the last group
    if current_group:
        groups.append(current_group)
    
    return groups

