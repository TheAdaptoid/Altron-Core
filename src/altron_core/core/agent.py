import json
from collections.abc import Generator
from enum import Enum
from os import getenv

from dotenv import load_dotenv

from altron_core.core.tooling import EventCallbacks, ToolExecutor
from altron_core.core.tools import calculator  # Ensure tools are registered
from altron_core.networking import lmstudio
from altron_core.types import Message
from altron_core.types.stream import ChoiceChunk, ToolCall
from altron_core.types.tools import ToolRequest, ToolResponse

load_dotenv()

DEFAULT_GENERALIST: str = "qwen/qwen3-4b-thinking-2507"  # "llama-3.2-3b-instruct"
DEFAULT_RESEARCHER: str = "openai/gpt-oss-20b"
DEFAULT_QUICK_RESPONDER: str = "google/gemma-3-1b"

DEFAULT_REASONING_INDICATOR: str = "THOUGHT"

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


class Agent:
    def __init__(self, role: AgentRole):
        self._role = role
        self._prompt = role_prompt_map(role)
        self._executor = ToolExecutor(tools=[calculator])
        self._event_callbacks = EventCallbacks()

    @property
    def role(self) -> AgentRole:
        """The role of the agent, which determines its behavior."""
        return self._role

    @role.setter
    def role(self, new_role: AgentRole) -> None:
        if not isinstance(new_role, AgentRole):
            raise ValueError(f"Invalid role: {new_role}")
        self._role = new_role
        self._prompt = role_prompt_map(new_role)

    def _process_tool_chunks(
        self,
        chunk: ChoiceChunk,
        prev_tool_request: ToolRequest | None,
        tool_requests: list[ToolRequest],
    ):
        tool_call: ToolCall = chunk["delta"]["tool_calls"][0]

        # If this is the first tool call, initialize the request
        if prev_tool_request is None:
            prev_tool_request = ToolRequest(
                id=tool_call["id"],
                name=tool_call["function"]["name"],
                arguments=tool_call["function"]["arguments"],
            )
            return

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
            return

        # If the tool call ID is the same, continue accumulating
        prev_tool_request["arguments"] += tool_call["function"]["arguments"]

    def _process_reasoning_chunks(
        self, chunk: ChoiceChunk, is_reasoning: bool
    ) -> tuple[Token, bool]:
        token: Token = chunk["delta"]["reasoning_content"]

        # Indicate start of reasoning
        if not is_reasoning:
            is_reasoning = True
            token = f"<{DEFAULT_REASONING_INDICATOR}>{token}"

        # Yield reasoning content
        return token, is_reasoning

    def _handle_content_chunks(
        self, chunk: ChoiceChunk, is_reasoning: bool
    ) -> tuple[Token, bool]:
        token: Token = chunk["delta"]["content"]

        # If we were in reasoning mode, exit it
        if is_reasoning:
            is_reasoning = False
            token = f"</{DEFAULT_REASONING_INDICATOR}>{token}"

        # Yield normal content
        return token, is_reasoning

    def _process_stream(
        self, stream: Generator[ChoiceChunk, None, str]
    ) -> Generator[Token, None, list[ToolRequest]]:
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
                self._process_tool_chunks(chunk, prev_tool_request, tool_requests)
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
        """Handle the tool requests by executing them."""
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

    def invoke(self, messages: list[Message]) -> Generator[Token, None, Message]:
        if not messages:
            raise ValueError("Message list cannot be empty.")

        # Make a copy to avoid modifying the original list
        _messages: list[Message] = messages.copy()

        # Insert the system prompt
        messages.insert(0, Message(role="system", content=self._prompt))

        # Start streaming the initial response
        initial_stream = self._process_stream(
            lmstudio.chat_stream(
                model_id=self._role.value,
                messages=_messages,
                tools=self._executor.get_schemas(),
            )
        )
        response_text: str = ""
        tool_requests: list[ToolRequest] = []
        while True:
            try:
                token: Token = next(initial_stream)
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
        self._event_callbacks.on_tool_request(tool_requests)
        tool_responses: list[ToolResponse] = self._handle_tool_requests(tool_requests)
        self._event_callbacks.on_tool_response(tool_responses)

        # Format the tool requests and responses
        request_message: Message = Message(
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
        final_stream = self.invoke(followup_messages)
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
