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

type ThreadId = str  # Alias for thread ID


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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        return cls(
            role=data["role"],
            text=data["text"],
            timestamp=data["timestamp"],
        )


@dataclass
class MessageThread:
    """
    A collection of messages exchanged between the user and the agent.

    Attributes:
        id (ThreadId): The unique identifier for the message thread.
            This is also the creation time in nanoseconds
            and the filename where the thread is stored.
        title (str): The title of the message thread.
        messages (list[Message]): The list of messages in the thread.
    """

    id: ThreadId
    title: str
    messages: list[Message] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MessageThread":
        return cls(
            id=data["id"],
            title=data["title"],
            messages=[Message.from_dict(msg) for msg in data["messages"]],
        )


@dataclass
class ConversePacket:
    """
    A collection of data representing an initial user query.

    Attributes:
        thread_id (str): The unique identifier for the message thread.
        message (Message): The initial user query.
    """

    thread_id: str
    message: Message

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConversePacket":
        return cls(
            thread_id=data["thread_id"],
            message=Message.from_dict(data["message"]),
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


@dataclass
class StreamStatePacket:
    """
    Represents the current state and minimal metadata for a processing stream.

    Attributes:
        curr_state (Literal["perceiving", "thinking", "acting", "responding", "failed", "done"]):
            The current lifecycle stage of the stream. Use this to determine what the
            system is currently doing (e.g., collecting input, reasoning, performing an action,
            composing a response, or finished/errored).
        error (str | None):
            Optional human-readable error message present when curr_state == "failed".
            Defaults to None.
        stream (Literal["active", "inactive"]):
            Indicates whether the stream is actively producing or consuming events.
            Defaults to "inactive".
        token (str | None):
            Optional opaque identifier used to correlate or authenticate a particular stream
            or message. Defaults to None.
        timestamp (str):
            ISO 8601 formatted timestamp representing when the packet was created. By default
            this is populated with datetime.now().isoformat() at instantiation time.

    Behavior and usage:
        - Use 'stream' for quick checks of activity, and 'curr_state' for more granular state logic.
        - When reporting failures, set curr_state to "failed" and provide details in 'error'.
        - The timestamp is intended for ordering and auditing; treat it as the authoritative
          creation time of the packet.
        - The object is suitable for lightweight serialization (e.g., JSON) for inter-component
          messaging and logging.

    Example:
        A typical packet signaling an active perception phase:
            StreamStatePacket(curr_state="perceiving", stream="active")
    """

    curr_state: Literal[
        "perceiving", "thinking", "acting", "responding", "failed", "done"
    ]
    error: str | None = None
    stream: Literal["active", "inactive"] = "inactive"
    token: str | None = None
    timestamp: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )  # ISO 8601 format


@dataclass
class TokenChunk:
    """
    Represents a small "chunk" of a token stream with optional semantic annotations.

    This lightweight container holds one portion of processed token data and up to two
    auxiliary annotations: an internal "thought" string and a serialized "tool_call".
    It is intended for use where token-level metadata needs to be carried alongside
    raw text (for example, during incremental generation, analysis, or logging).

    Attributes:
        content (str | None): The literal token text for this chunk. May be None when
            the chunk only carries metadata.
        thought (str | None): An optional internal or agent "thought" associated with
            the token chunk (e.g., reasoning, debug notes, or intermediate state).
        tool_call (str | None): An optional serialized representation of a tool call
            triggered or referenced by this chunk (e.g., JSON or CLI-like string).

    Notes:
        - Any combination of fields may be set; in typical usage only one of
          content, thought, or tool_call is populated for a given chunk.
        - Consumers should treat the fields as simple containers and apply higher-level
          validation (such as mutually exclusive semantics) where appropriate.

    Example:
        >>> TokenChunk(content="Hello")
        >>> TokenChunk(thought="consider next token")
        >>> TokenChunk(tool_call='{"name":"lookup","args":{"q":"foo"}}')
    """

    content: str | None = None
    thought: str | None = None
    tool_call: str | None = None
