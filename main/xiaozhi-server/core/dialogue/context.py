"""
Chat context management

Manages dialogue history as a list of ChatItems.
"""

from typing import Any

from .content import ChatContent
from .items import ChatItem, ChatMessage, FunctionCall, FunctionCallOutput


class ChatContext:
    """
    Standard chat context (provider-agnostic)
    
    Manages dialogue history as a list of ChatItems.
    """

    def __init__(self, items: list[ChatItem] | None = None):
        self._items: list[ChatItem] = items or []

    @classmethod
    def empty(cls) -> "ChatContext":
        """Create an empty context"""
        return cls([])

    @property
    def items(self) -> list[ChatItem]:
        """Get all items"""
        return self._items

    def add_message(
        self,
        role: str,
        content: ChatContent | list[ChatContent],
        **kwargs: Any
    ) -> ChatMessage:
        """
        Add a message to the context
        
        Args:
            role: Message role (system, user, assistant, developer)
            content: Message content (string or list of content items)
            **kwargs: Additional fields for ChatMessage
        
        Returns:
            The created ChatMessage
        """
        # Normalize content to list
        if isinstance(content, (str, dict)):
            content_list = [content]
        else:
            content_list = list(content)

        message = ChatMessage(role=role, content=content_list, **kwargs)
        self._items.append(message)
        return message

    def add_function_call(
        self,
        call_id: str,
        name: str,
        arguments: str,
        **kwargs: Any
    ) -> FunctionCall:
        """
        Add a function call
        
        Args:
            call_id: Unique call identifier
            name: Function name
            arguments: Function arguments (JSON string)
            **kwargs: Additional fields for FunctionCall
        
        Returns:
            The created FunctionCall
        """
        func_call = FunctionCall(
            call_id=call_id,
            name=name,
            arguments=arguments,
            **kwargs
        )
        self._items.append(func_call)
        return func_call

    def add_function_output(
        self,
        call_id: str,
        name: str,
        output: str,
        is_error: bool = False,
        **kwargs: Any
    ) -> FunctionCallOutput:
        """
        Add function call output
        
        Args:
            call_id: Call identifier (matches FunctionCall.call_id)
            name: Function name
            output: Function result (string)
            is_error: Whether the output represents an error
            **kwargs: Additional fields for FunctionCallOutput
        
        Returns:
            The created FunctionCallOutput
        """
        func_output = FunctionCallOutput(
            call_id=call_id,
            name=name,
            output=output,
            is_error=is_error,
            **kwargs
        )
        self._items.append(func_output)
        return func_output

    def copy(self) -> "ChatContext":
        """Create a shallow copy of the context"""
        return ChatContext(self._items.copy())

    def clear(self) -> None:
        """Clear all items"""
        self._items.clear()

    def __len__(self) -> int:
        """Return number of items"""
        return len(self._items)

    def __repr__(self) -> str:
        return f"ChatContext(items={len(self._items)})"

