from typing import TypedDict


class ToolRequest(TypedDict):
    id: str
    name: str
    arguments: str  # JSON string of arguments


class ToolResponse(TypedDict):
    id: str
    name: str
    content: str  # The response content from the tool
