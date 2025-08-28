from typing import Literal, NotRequired, TypedDict

from altron_core.types.tools import ToolCall

ROLE = Literal["user", "assistant", "system", "tool"]
"""The role of the entity sending the message."""


class Message(TypedDict):
    """
    Represents a message exchanged in a conversation.

    Attributes:
        role (ROLE): The role of the entity sending the message (e.g., user, assistant).
        content (str): The textual content of the message.
    """

    role: ROLE
    content: str
    tool_calls: NotRequired[list[ToolCall]]  # List of tool calls, if any
    tool_call_id: NotRequired[str]  # ID of the tool call, if applicable
