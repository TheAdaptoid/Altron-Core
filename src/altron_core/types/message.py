from typing import Literal, TypedDict

ROLE = Literal["user", "assistant", "system"]
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
