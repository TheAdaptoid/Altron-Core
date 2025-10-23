from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal


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
    role: Literal["user", "agent"]
    timestamp: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )  # ISO 8601 format


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
