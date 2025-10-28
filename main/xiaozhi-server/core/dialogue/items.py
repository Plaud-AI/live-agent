"""
Standard chat item definitions

Defines the core types of items that can appear in a chat context:
- ChatMessage: User or assistant messages
- FunctionCall: Function/tool invocations
- FunctionCallOutput: Results from function calls
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Union

from .content import ChatContent


def _generate_id(prefix: str) -> str:
    """Generate a simple unique ID"""
    import uuid
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


@dataclass
class ChatMessage:
    """
    Standard chat message
    
    Represents a message from user, assistant, or system.
    """

    id: str = field(default_factory=lambda: _generate_id("msg"))
    type: Literal["message"] = "message"
    role: Literal["system", "user", "assistant", "developer"] = "user"
    content: list[ChatContent] = field(default_factory=list)
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())

    # Optional fields
    interrupted: bool = False


@dataclass
class FunctionCall:
    """
    Function call
    
    Represents a tool/function invocation. Does not distinguish between
    local functions, MCP tools, or other implementations at protocol level.
    """

    id: str = field(default_factory=lambda: _generate_id("fc"))
    type: Literal["function_call"] = "function_call"
    call_id: str = field(default_factory=lambda: _generate_id("call"))
    name: str = ""
    arguments: str = ""  # JSON string
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())


@dataclass
class FunctionCallOutput:
    """Function call result"""

    id: str = field(default_factory=lambda: _generate_id("fco"))
    type: Literal["function_call_output"] = "function_call_output"
    call_id: str = ""
    name: str = ""
    output: str = ""
    is_error: bool = False
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())


# Union type for all chat items
ChatItem = Union[ChatMessage, FunctionCall, FunctionCallOutput]

