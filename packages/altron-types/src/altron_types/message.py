from datetime import datetime
from enum import Enum

from pydantic import Field

from altron_types.utils import ModelBase


class MessageRole(str, Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


class MessageContent(ModelBase):
    text: str = Field(..., description="Text content of the message", frozen=True)


class Message(ModelBase):
    id: str = Field(..., description="Unique identifier for the message", frozen=True)
    role: MessageRole = Field(
        ..., description="Role of the sender (e.g., user, assistant)", frozen=True
    )
    content: MessageContent = Field(
        ..., description="Content of the message", frozen=True
    )
    timestamp: str = Field(
        description="Timestamp of the message",
        frozen=True,
        default_factory=datetime.now().isoformat,
    )
