from fastapi import APIRouter
from pydantic import BaseModel, Field


class DiscordMessage(BaseModel):
    """
    A Discord message.

    Attributes:
        sender (str): The sender of the message.
        text (str): The text content of the message.
        image (bytes | str | None, optional): The image content of the message.
    """

    sender: str = Field(..., description="The sender of the message.")
    text: str = Field(..., description="The text content of the message.")
    image: bytes | str | None = Field(
        default=None, description="The image content of the message."
    )


router = APIRouter(
    prefix="/discord",
    tags=["discord"],
)


@router.get("/ping")
async def ping() -> str:
    """Check if the altron server is running."""
    return "pong"


@router.post("/message")
async def message(messages: list[DiscordMessage]) -> DiscordMessage:
    """
    Send a list of Discord messages to Altron.

    Returns:
        DiscordMessage: A Discord message with the sender set to "Altron".
    """
    # TODO: implement
    return DiscordMessage(
        sender="Altron",
        text="Hello from Altron!",
    )
