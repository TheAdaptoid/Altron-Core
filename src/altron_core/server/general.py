from fastapi import APIRouter
from pydantic import BaseModel, Field


class Message(BaseModel):
    role: str = Field(..., description="The role of the message sender.")
    text: str = Field(..., description="The text content of the message.")


router = APIRouter(
    prefix="/altron",
    tags=["altron"],
)


@router.post("/quick")
async def quick(messages: list[Message]) -> Message:
    # TODO: implement
    return Message(role="assistant", text="Hello from Altron!")


@router.post("/converse")
async def converse(messages: list[Message]) -> Message:
    # TODO: implement
    return Message(role="assistant", text="Hello from Altron!")
