from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessage,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

EMPTY_MESSAGE_TEXT = "[[No Text Content]]"


@dataclass
class Message:
    """
    A message from either the user or the agent.

    Attributes:
        text (str): The text of the message.
        role (Literal["user", "agent"]): The role of the message sender.
        timestamp (str):
            The creation timestamp of the message in ISO 8601 format.
    """

    text: str
    role: Literal["user", "agent", "system"]
    timestamp: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )  # ISO 8601 format

    def to_openai_spec(self) -> ChatCompletionMessageParam:
        """
        Convert a Message object to a ChatCompletionMessageParam.

        Returns the equivalent OpenAI spec message param for the given message.
        Raises a ValueError if the message role is not recognized.
        """
        if self.role == "user":
            return ChatCompletionUserMessageParam(
                role=self.role,
                content=self.text,
            )
        elif self.role == "agent":
            return ChatCompletionAssistantMessageParam(
                role="assistant",
                content=self.text,
            )
        elif self.role == "system":
            return ChatCompletionSystemMessageParam(
                role=self.role,
                content=self.text,
            )
        else:
            raise ValueError(f"Unsupported Message role: {self.role}")

    @classmethod
    def from_openai_spec(cls, msg: ChatCompletionMessage) -> "Message":
        """
        Create a Message object from a ChatCompletionMessage.

        Args:
            msg (ChatCompletionMessage): The OpenAI spec message to convert.

        Returns:
            Message: The equivalent Message object.
        """
        return cls(
            role="agent" if msg.role == "assistant" else msg.role,
            text=msg.content or EMPTY_MESSAGE_TEXT,
        )


@dataclass
class ActionPacket:
    """
    A collection of data representing an action taken by the agent.

    Attributes:
        tool_name (str): The name of the tool being used.
        tool_input (dict[str, Any]): The input provided to the tool.
        tool_output (Any | None): The output returned by the tool, if any.
        timestamp (str):
            The creation timestamp of the action packet in ISO 8601 format.
    """

    tool_name: str
    tool_input: dict[str, Any]
    tool_output: Any | None = None
    timestamp: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )  # ISO 8601 format


@dataclass
class StatePacket:
    """
    A collection of data representing the previous state of the agent.

    Provides context about what the agent just finished doing at a given moment.
    Packets are yield after each state transition in the agent's lifecycle.

    Attributes:
        prev_state (Literal["thinking", "perceiving", "acting", "responding", "failed"]):
            The previous state of the agent.
        next_state (Literal["thinking", "perceiving", "acting", "responding"]):
            The next, most likely, state of the agent.
        details (Any | None):
            Additional details about the previous state.
        timestamp (str):
            The creation timestamp of the state packet in ISO 8601 format.
    """

    prev_state: Literal["thinking", "perceiving", "acting", "responding", "failed"]
    next_state: Literal["thinking", "perceiving", "acting", "responding"]
    details: Any | list[ActionPacket] | None = None
    timestamp: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )  # ISO 8601 format
