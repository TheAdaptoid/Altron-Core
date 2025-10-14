from fastapi import APIRouter
from pydantic import BaseModel, Field


class Message(BaseModel):
    role: str = Field(..., description="The role of the message sender.")
    text: str = Field(..., description="The text content of the message.")


router = APIRouter(
    prefix="/altron",
    tags=["altron"],
)


@router.post("/chat")
async def chat(messages: list[Message]) -> Message:
    # TODO: implement
    return Message(role="assistant", text="Hello from Altron!")


@router.post("/create_thread")
async def create_thread(title: str | None = None) -> str:
    # TODO: implement
    return "Thread ID"


@router.get("/get_thread")
async def get_thread(thread_id: str) -> list[Message]:
    # TODO: implement
    return []


@router.patch("/update_thread")
async def update_thread(thread_id: str, new_title: str) -> str:
    # TODO: implement
    return "Thread ID"


@router.delete("/delete_thread")
async def delete_thread(thread_id: str) -> None:
    # TODO: implement
    pass


@router.post("/converse")
async def converse(thread_id: str, message: Message) -> Message:
    # TODO: implement
    return Message(role="assistant", text="Hello from Altron!")
