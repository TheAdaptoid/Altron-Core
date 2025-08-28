import json
from os import getenv
from typing import Any, cast

from dotenv import load_dotenv
from requests import Response, post

from altron_core.types.chunks import CompletionChunk
from altron_core.types.message import Message
from altron_core.types.streams import ChatStream

load_dotenv()

CHAT_ENDPOINT: str = "/api/v0/chat/completions"


def chat(
    model_id: str, messages: list[Message], tools: list[dict[str, Any]] | None = None
) -> ChatStream:
    """
    Send a chat request to the language model server and streams the response.

    Args:
        model_id (str): The identifier of the model to use for inference.
        messages (list[Message]):
            A list of message objects representing the conversation history.
        tools (list[dict[str, Any]] | None, optional):
            A list of tool specifications to provide to the model. Defaults to None.

    Yields:
        dict: The next chunk of the model's response, typically a message choice.

    Returns:
        str: "Done" when the streaming is complete.

    Raises:
        HTTPError: If the HTTP request to the model server fails.
    """
    url: str = f"{getenv('LMSTUDIO_HOST', 'http://localhost:1234')}{CHAT_ENDPOINT}"
    response: Response = post(
        url=url,
        json={
            "model": model_id,
            "messages": messages,
            "tools": tools,
            "stream": True,
        },
        stream=True,
    )

    # Check for errors
    response.raise_for_status()

    for chunk in response.iter_content(chunk_size=8192):
        if chunk is None:
            print("No Data")
            continue

        chunk = cast(bytes, chunk)
        text: str = chunk.decode("utf-8").replace("data: ", "").replace("\n\n", "")

        if text == "[DONE]":
            return "Done"

        obj = json.loads(text)
        cc = CompletionChunk(**obj)
        yield cc["choices"][0]

    return "Done"
