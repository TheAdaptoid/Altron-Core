from typing import Literal, TypedDict

FINISH_REASON = Literal["stop", "length", None]


class ToolCallFunction(TypedDict):
    name: str
    arguments: str  # JSON string of arguments


class ToolCall(TypedDict):
    id: str
    type: Literal["function"]
    function: ToolCallFunction


class ChoiceDelta(TypedDict):
    role: str
    content: str
    tool_calls: list[ToolCall]


class ChoiceChunk(TypedDict):
    index: int
    delta: ChoiceDelta
    logprobs: None
    finish_reason: FINISH_REASON


class CompletionChunk(TypedDict):
    id: str
    object: str
    created: int
    model: str
    system_fingerprint: str
    choices: list[ChoiceChunk]
