from typing import Literal, TypedDict


class ToolCallFunction(TypedDict):
    name: str
    arguments: str  # JSON string of arguments


class ToolCall(TypedDict):
    id: str
    type: Literal["function"]
    function: ToolCallFunction


class ToolRequest(TypedDict):
    id: str
    name: str
    arguments: str  # JSON string of arguments


class ToolResponse(TypedDict):
    id: str
    name: str
    content: str  # The response content from the tool


class ToolParameter(TypedDict):
    name: str
    description: str
    type: Literal["string", "integer", "number", "boolean"]
    required: bool


class ToolSchema(TypedDict):
    name: str
    description: str
    parameters: list[ToolParameter]
