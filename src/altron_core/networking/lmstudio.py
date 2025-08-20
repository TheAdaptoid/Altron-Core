import json
from collections.abc import Generator, Iterator
from os import getenv
from typing import Any, cast

from dotenv import load_dotenv
from requests import post

from altron_core.types import CompletionChunk, Message
from altron_core.types.stream import ChoiceChunk

load_dotenv()

CHAT_ENDPOINT: str = "/api/v0/chat/completions"


class ResponseStream:
    def __init__(self, iter: Iterator[CompletionChunk]) -> None:
        self._iter = iter

    def next(self) -> CompletionChunk:
        """Get the next chunk from the stream."""
        try:
            return next(self._iter)
        except StopIteration:
            raise ValueError("No more chunks in the stream.")


def display_chars(text: str):
    for idx, char in enumerate(text):
        print(f"{idx}: {char}")


def chat(model_id: str, messages: list[Message]) -> Message:
    url: str = f"{getenv('LMSTUDIO_HOST', 'http://localhost:1234')}{CHAT_ENDPOINT}"
    response = post(
        url=url,
        json={
            "model": model_id,
            "messages": messages,
            "stream": False,
        },
        stream=True,
    )

    # Check for errors
    response.raise_for_status()

    completion: dict[str, Any] = response.json()
    choice = completion["choices"][0]
    message = choice["message"]
    return Message(**message)


def chat_stream(
    model_id: str, messages: list[Message], tools: list[dict[str, Any]] | None = None
) -> Generator[ChoiceChunk, None, str]:
    url: str = f"{getenv('LMSTUDIO_HOST', 'http://localhost:1234')}{CHAT_ENDPOINT}"
    response = post(
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
        text = chunk.decode("utf-8").replace("data: ", "").replace("\n\n", "")

        if text == "[DONE]":
            return "Done"

        obj = json.loads(text)
        cc = CompletionChunk(**obj)
        yield cc["choices"][0]

    return "Done"
