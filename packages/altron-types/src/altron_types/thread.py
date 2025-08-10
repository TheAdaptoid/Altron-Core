from pydantic import Field

from altron_types.message import Message
from altron_types.utils import ModelBase


class Thread(ModelBase):
    id: str = Field(..., description="Unique identifier for the thread", frozen=True)
    title: str = Field(..., description="Title of the thread", frozen=True)
    created_at: str = Field(
        ..., description="Creation timestamp of the thread", frozen=True
    )
    updated_at: str = Field(
        ..., description="Last updated timestamp of the thread", frozen=True
    )
    messages: list[Message] = Field(
        ..., description="List of messages in the thread", frozen=True
    )
    message_count: int = Field(
        ..., description="Number of messages in the thread", frozen=True
    )
    token_count: int = Field(
        ..., description="Total token count in the thread", frozen=True
    )
