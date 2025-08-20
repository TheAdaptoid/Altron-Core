import json
from collections.abc import Generator
from enum import Enum
from os import getenv
from typing import Any, Literal, TypedDict

from dotenv import load_dotenv

from altron_core.networking import lmstudio
from altron_core.types import Message
from altron_core.types.stream import ChoiceChunk, ToolCall
from altron_core.types.tools import ToolRequest

load_dotenv()

DEFAULT_GENERALIST: str = "llama-3.2-3b-instruct"
DEFAULT_RESEARCHER: str = "openai/gpt-oss-20b"
DEFAULT_QUICK_RESPONDER: str = "google/gemma-3-1b"

type Token = str


class ModelLoadError(Exception):
    def __init__(self, model_id: str, fail_reason: str) -> None:
        super().__init__(f"Failed to load model '{model_id}': {fail_reason}")


class AgentRole(str, Enum):
    GENERALIST = getenv("GENERALIST_MODEL", DEFAULT_GENERALIST)
    RESEARCHER = getenv("RESEARCHER_MODEL", DEFAULT_RESEARCHER)
    QUICK_RESPONDER = getenv("QUICK_RESPONDER_MODEL", DEFAULT_QUICK_RESPONDER)


def role_prompt_map(role: AgentRole) -> str:
    """Retrieve the prompt template for the given agent role."""
    if role == AgentRole.GENERALIST:
        return "You are a generalist agent. Your task is to assist with a wide range of queries."
    elif role == AgentRole.RESEARCHER:
        return "You are a researcher agent. Your task is to provide in-depth information and analysis."
    elif role == AgentRole.QUICK_RESPONDER:
        return "You are a quick responder agent. Your task is to provide fast and concise answers."
    else:
        raise ValueError(f"Unknown agent role: {role}")


class ToolParameter(TypedDict):
    name: str
    description: str
    type: Literal[
        "string", "integer", "number", "boolean"
    ]  # e.g., "string", "integer", "boolean", etc
    required: bool


class Tool(TypedDict):
    name: str
    description: str
    parameters: list[ToolParameter]


class ToolExecutor:
    def convert_to_common_schema(self, tool: Tool) -> dict[str, Any]:
        """Convert a tool to a common schema for execution."""
        required: list[str] = []
        properties: dict[str, dict[str, Any]] = {}

        for param in tool["parameters"]:
            # Get the details of the parameter
            properties[param["name"]] = {
                "type": param["type"],
                "description": param["description"],
            }

            # Check if the parameter is required
            if param.get("required", False):
                required.append(param["name"])

        return {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }

    def get_tools(self) -> list[dict[str, Any]]:
        calculator_tool: Tool = {
            "name": "calculator",
            "description": "A tool to perform basic arithmetic operations.",
            "parameters": [
                {
                    "name": "operation",
                    "description": "The arithmetic operation to perform (add, subtract, multiply, divide).",
                    "type": "string",
                    "required": True,
                },
                {
                    "name": "a",
                    "description": "The first number.",
                    "type": "number",
                    "required": True,
                },
                {
                    "name": "b",
                    "description": "The second number.",
                    "type": "number",
                    "required": True,
                },
            ],
        }
        tools: list[Tool] = [calculator_tool]

        return [self.convert_to_common_schema(tool) for tool in tools]

    def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Execute a tool with the given name and arguments."""
        print(f"Executing tool: {tool_name} with arguments: {arguments}")


class Agent:
    def __init__(self, role: AgentRole):
        self._role = role
        self._prompt = role_prompt_map(role)
        self._executor = ToolExecutor()

    @property
    def role(self) -> AgentRole:
        return self._role

    @role.setter
    def role(self, new_role: AgentRole) -> None:
        self._role = new_role
        self._prompt = role_prompt_map(new_role)

    def _insert_system_prompt(self, messages: list[Message]) -> None:
        first_message = messages[0]
        if first_message["role"] == "system":
            return

        system_prompt = Message(role="system", content=self._prompt)
        messages.insert(0, system_prompt)

    def _process_stream(
        self, stream: Generator[ChoiceChunk, None, str]
    ) -> Generator[Token, None, list[ToolRequest]]:
        """Process the stream of response chunks."""
        prev_tool_request: ToolRequest | None = None
        tool_requests: list[ToolRequest] = []

        for chunk in stream:
            if not chunk["delta"]:
                break

            # Check if the response is a tool call
            if "tool_calls" in chunk["delta"]:
                tool_calls: list[ToolCall] = chunk["delta"]["tool_calls"]
                tool_call: ToolCall = tool_calls[0]

                # If this is the first tool call, initialize the request
                if prev_tool_request is None:
                    prev_tool_request = ToolRequest(
                        id=tool_call["id"],
                        name=tool_call["function"]["name"],
                        arguments=tool_call["function"]["arguments"],
                    )
                    continue

                # If the tool call ID has changed,
                # save the previous request,
                # and start a new one
                if "id" in tool_call and prev_tool_request["id"] != tool_call["id"]:
                    tool_requests.append(prev_tool_request)
                    prev_tool_request = ToolRequest(
                        id=tool_call["id"],
                        name=tool_call["function"]["name"],
                        arguments=tool_call["function"]["arguments"],
                    )
                    continue
                # If the tool call ID is the same, continue accumulating
                prev_tool_request["arguments"] += tool_call["function"]["arguments"]
            else:
                token: Token = chunk["delta"]["content"]
                yield token

        # Handle any remaining tool requests
        if prev_tool_request is not None:
            tool_requests.append(prev_tool_request)

        return tool_requests

    def _handle_tool_requests(self, tool_requests: list[ToolRequest]) -> None:
        """Handle the tool requests by executing them."""
        for request in tool_requests:
            self._executor.execute_tool(
                tool_name=request["name"],
                arguments=json.loads(request["arguments"]),
            )

    def invoke_stream(self, messages: list[Message]) -> Generator[Token, None, Message]:
        if not messages:
            raise ValueError("Message list cannot be empty.")

        self._insert_system_prompt(messages)

        stream = lmstudio.chat_stream(
            model_id=self._role.value,
            messages=messages,
            tools=self._executor.get_tools(),
        )
        stream_processor = self._process_stream(stream)

        response_text: str = ""

        while True:
            try:
                token: Token = next(stream_processor)
                response_text += token
                yield token
            except StopIteration as e:
                tool_requests: list[ToolRequest] = e.value
                break
        yield "\n"  # Send a new line for easier formatting by the user

        # Handle any tool requests that were made during the stream
        if tool_requests:
            self._handle_tool_requests(tool_requests)

        return Message(role="assistant", content=response_text)
