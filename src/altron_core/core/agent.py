import json
from collections.abc import Generator
from enum import Enum
from os import getenv

from dotenv import load_dotenv

from altron_core.core.tooling import Tool, ToolExecutor
from altron_core.core.tools import calculator  # Ensure tools are registered
from altron_core.networking import inference
from altron_core.types.chunks import ChoiceChunk, ToolCall
from altron_core.types.message import Message
from altron_core.types.streams import InvocationStream
from altron_core.types.tools import ToolRequest, ToolResponse

load_dotenv()

DEFAULT_GENERALIST: str = "qwen/qwen3-4b-thinking-2507"
DEFAULT_RESEARCHER: str = "openai/gpt-oss-20b"
DEFAULT_QUICK_RESPONDER: str = "google/gemma-3-1b"

DEFAULT_REASONING_INDICATOR: str = "THOUGHT"
DEFAUTL_TOOL_CALL_INDICATOR: str = "TOOL_CALL"


class AgentRole(str, Enum):
    """
    An enumeration representing different roles an agent can assume within the system.

    Attributes:
        GENERALIST: Represents a generalist agent model.
        RESEARCHER: Represents a researcher agent model.
        QUICK_RESPONDER: Represents a quick responder agent model.
    """

    GENERALIST = getenv("GENERALIST_MODEL", DEFAULT_GENERALIST)
    RESEARCHER = getenv("RESEARCHER_MODEL", DEFAULT_RESEARCHER)
    QUICK_RESPONDER = getenv("QUICK_RESPONDER_MODEL", DEFAULT_QUICK_RESPONDER)


def prompt_tool_map(role: AgentRole) -> tuple[str, list[Tool]]:
    """
    Retrieve the prompt template and the tool set for the given agent role.

    Raises:
        ValueError: If the role is unknown
    """
    match role:
        case AgentRole.GENERALIST:
            return (
                "You are a generalist agent."
                "Your task is to assist with a wide range of queries."
            ), [calculator]
        case AgentRole.RESEARCHER:
            return (
                "You are a researcher agent."
                "Your task is to provide in-depth information and analysis."
            ), []
        case AgentRole.QUICK_RESPONDER:
            return (
                "You are a quick responder agent."
                "Your task is to provide fast and concise answers."
            ), [calculator]
        case _:
            raise ValueError(f"Unknown agent role: {role}")


class Agent:
    def __init__(self, role: AgentRole):
        self._role = role
        self._prompt, tools = prompt_tool_map(role)
        self._executor = ToolExecutor(tools=tools)

    @property
    def role(self) -> AgentRole:
        """The role of the agent, which determines its behavior."""
        return self._role

    @role.setter
    def role(self, new_role: AgentRole) -> None:
        if not isinstance(new_role, AgentRole):
            raise ValueError(f"Invalid role: {new_role}")
        self._role = new_role
        self._prompt, tools = prompt_tool_map(new_role)
        self._executor.set_tools(new_tools=tools)

    def _process_tool_chunks(
        self,
        chunk: ChoiceChunk,
        prev_tool_request: ToolRequest | None,
        tool_requests: list[ToolRequest],
    ) -> ToolRequest:
        tool_call: ToolCall = chunk["delta"]["tool_calls"][0]

        # If this is the first tool call, initialize the request
        if prev_tool_request is None:
            if ("id" not in tool_call) or ("name" not in tool_call["function"]):
                raise ValueError(
                    f"Invalid Tool Call Shape: {json.dumps(tool_call, indent=2)}"
                )
            return ToolRequest(
                id=tool_call["id"],
                name=tool_call["function"]["name"],
                arguments=tool_call["function"]["arguments"],
            )

        # If the tool call ID has changed,
        # save the previous request,
        # and start a new one
        if "id" in tool_call and prev_tool_request["id"] != tool_call["id"]:
            tool_requests.append(prev_tool_request)
            return ToolRequest(
                id=tool_call["id"],
                name=tool_call["function"]["name"],
                arguments=tool_call["function"]["arguments"],
            )

        # If the tool call ID is the same, continue accumulating
        prev_tool_request["arguments"] += tool_call["function"]["arguments"]
        return prev_tool_request

    def _process_reasoning_chunks(
        self, chunk: ChoiceChunk, is_reasoning: bool
    ) -> tuple[str, bool]:
        token: str = chunk["delta"]["reasoning_content"]

        # Indicate start of reasoning
        if not is_reasoning:
            is_reasoning = True
            token = f"<{DEFAULT_REASONING_INDICATOR}>{token}"

        # Yield reasoning content
        return token, is_reasoning

    def _handle_content_chunks(
        self, chunk: ChoiceChunk, is_reasoning: bool
    ) -> tuple[str, bool]:
        token: str = chunk["delta"]["content"]

        # If we were in reasoning mode, exit it
        if is_reasoning:
            is_reasoning = False
            token = f"</{DEFAULT_REASONING_INDICATOR}>{token}"

        # Yield normal content
        return token, is_reasoning

    def _process_stream(
        self, stream: Generator[ChoiceChunk, None, str]
    ) -> Generator[str, None, list[ToolRequest]]:
        """
        Process a stream of response chunks, to yield tokens and return tool requests.

        This generator function iterates over a stream of response chunks,
        handling three types of content:
        - Tool calls: Accumulates tool requests, grouping arguments by tool call ID.
        - Normal content: Yields tokens as they are received.
        - Reasoning content: Yields tokens wrapped with reasoning indicators.

        At the end of the stream, any remaining tool requests are returned as a list.

        Args:
            stream (Generator[ChoiceChunk, None, str]):
                A generator yielding response chunks.

        Yields:
            Token: Tokens from the response stream,
                including reasoning and normal content.

        Returns:
            list[ToolRequest]:
                A list of accumulated tool requests after processing the stream.

        Raises:
            ValueError: If a chunk with an unexpected format is encountered.
        """
        prev_tool_request: ToolRequest | None = None
        tool_requests: list[ToolRequest] = []
        is_reasoning: bool = False

        for chunk in stream:
            if not chunk["delta"]:
                break

            # Check if the response is a tool call
            if "tool_calls" in chunk["delta"]:
                prev_tool_request = self._process_tool_chunks(
                    chunk, prev_tool_request, tool_requests
                )
            elif "content" in chunk["delta"]:
                token, is_reasoning = self._handle_content_chunks(chunk, is_reasoning)
                yield token
            elif "reasoning_content" in chunk["delta"]:
                token, is_reasoning = self._process_reasoning_chunks(
                    chunk, is_reasoning
                )
                yield token
            else:
                raise ValueError(
                    f"Unexpected chunk format. {json.dumps(chunk, indent=2)}"
                )

        # Append any remaining tool requests
        if prev_tool_request is not None:
            tool_requests.append(prev_tool_request)

        return tool_requests

    def _handle_tool_requests(
        self, tool_requests: list[ToolRequest]
    ) -> list[ToolResponse]:
        """Handle tool requests by executing them."""
        tool_responses: list[ToolResponse] = []
        for request in tool_requests:
            result = self._executor.execute_tool(
                tool_name=request["name"],
                arguments=json.loads(request["arguments"]),
            )
            tool_responses.append(
                ToolResponse(
                    id=request["id"],
                    name=request["name"],
                    content=result,
                )
            )
        return tool_responses

    def _yield_tool_requests(
        self, tool_requests: list[ToolRequest]
    ) -> Generator[str, None, Message]:
        req_msg: Message = Message(
            role="assistant",
            content="",
            tool_calls=[
                {
                    "id": req["id"],
                    "type": "function",
                    "function": {
                        "name": req["name"],
                        "arguments": req["arguments"],
                    },
                }
                for req in tool_requests
            ],
        )

        if "tool_calls" in req_msg:
            yield (
                f"<{DEFAUTL_TOOL_CALL_INDICATOR}>"
                f"{json.dumps(req_msg['tool_calls'], indent=2)}"
                f"</{DEFAUTL_TOOL_CALL_INDICATOR}>"
            )

        return req_msg

    def invoke(self, messages: list[Message]) -> InvocationStream:
        if not messages:
            raise ValueError("Message list cannot be empty.")

        # Make a copy to avoid modifying the original list
        _messages: list[Message] = messages.copy()

        # Insert the system prompt
        messages.insert(0, Message(role="system", content=self._prompt))

        # Start streaming the initial response
        initial_stream = self._process_stream(
            inference.chat(
                model_id=self._role.value,
                messages=_messages,
                tools=self._executor.get_schemas(),
            )
        )
        response_text: str = ""
        tool_requests: list[ToolRequest] = []
        while True:
            try:
                token: str = next(initial_stream)
                response_text += token
                yield token
            except StopIteration as e:
                tool_requests = e.value
                break
        yield "\n"  # Send a new line for easier formatting by the user

        # If there are no tool requests, return the response
        if not tool_requests:
            return Message(role="assistant", content=response_text)

        # If there are tool requests, handle them
        request_message: Message = yield from self._yield_tool_requests(tool_requests)
        tool_responses: list[ToolResponse] = self._handle_tool_requests(tool_requests)

        # Format the tool requests and responses
        response_messages: list[Message] = [
            Message(
                role="tool",
                content=resp["content"],
                tool_call_id=resp["id"],
            )
            for resp in tool_responses
        ]

        # Continue the conversation with the tool interactions
        followup_messages: list[Message] = (
            _messages + [request_message] + response_messages
        )
        final_stream: InvocationStream = self.invoke(followup_messages)
        response_text = ""
        while True:
            try:
                token = next(final_stream)
                response_text += token
                yield token
            except StopIteration as e:
                final_response: Message = e.value
                break
        yield "\n"  # Send a new line for easier formatting by the user
        return final_response
