import os
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator

from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import (
    ChatCompletionMessageParam,
)

from altron_core.types.dtypes import Message, TokenChunk


def get_lmstudio_url() -> str:
    """
    Return the URL of the LM Studio instance.

    Raises:
        ValueError: If the LM_STUDIO_HOST environment variable is not set.

    Returns:
        str: The URL of the LM Studio instance.
    """
    load_dotenv()
    host_port: str | None = os.getenv("LM_STUDIO_HOST")

    if host_port is None:
        raise ValueError("LM_STUDIO_HOST environment variable is not set.")

    return f"http://{host_port}/v1"


class InferenceEngine(ABC):
    """
    Abstract base for pluggable inference engines.

    Implementations of this class encapsulate the logic required to send a conversation
    context to a model backend (remote or local) and expose the model's incremental
    output as an async generator of TokenChunk objects. The generator yields partial
    token deltas as they arrive and yields a terminal None sentinel when the stream is
    complete.

    Notes and recommendations
    - Keep per-token processing lightweight to avoid backpressure;
        buffer or batch heavier work outside of the critical read loop.
    - Consider exposing metrics (latency, throughput, error counts)
        at implementation-level.
    - Document any backend-specific limitations
        (max tokens, supported model_ids, rate limits).
    """

    @abstractmethod
    def infer_stream(
        self, model_id: str, context: list[Message]
    ) -> AsyncGenerator[TokenChunk | None, None]:
        """
        Asynchronously stream tokenized output from a language model completion.

        This async generator converts the provided context into the OpenAI-compatible
        message format, invokes the client's chat completion API with streaming
        enabled, and yields TokenChunk objects as incremental pieces of the model's
        response arrive. A final None sentinel is yielded to indicate the end of the
        stream.

        Parameters
        ----------
        model_id : str
            Identifier of the model to use for the completion.
        context : list[Message]
            Sequence of IMessage/Message objects representing the conversation history.
            Each message is converted via Message.to_openai_spec() before being sent.

        Yields
        ------
        TokenChunk | None
            - TokenChunk instances containing partial output:
                - content: textual token content (may be None for non-text deltas)
                - thought: reasoning or "thought" content if provided by the model
                - tool_call: tool usage info (currently not parsed; may be None)
            - A final None value is yielded to explicitly mark the end of the stream.

        Behavior & Notes
        ----------------
        - The underlying client call uses stream=True and iterates over response chunks.
        - Each incoming chunk is expected at chunk.choices[0].delta and is converted
          to a dict via model_dump(). The relevant fields are mapped into TokenChunk.
        - If a chunk contains no content, thought, or tool_call, the generator stops
          iterating and closes the response stream.
        - The response stream is closed after iteration completes. If the client raises
          an exception, it will propagate to the caller (the generator will not yield
          further items unless the exception is handled externally).
        - The generator may perform network I/O and should be consumed with "async for".

        Example
        -------
        async for token in infer_stream(model_id, context):
            if token is None:
            process_token(token)
        """
        pass


class LMStudio_IE(InferenceEngine):
    """
    An InferenceEngine implementation that streams from an LM Studio instance.

    This class wraps an OpenAI client configured for LM Studio and provides an
    asynchronous generator interface to consume partial model output
    (token-level deltas) as they arrive.

    Attributes:
        client: An OpenAI-compatible client instance configured to communicate
            with LM Studio. The client is expected to expose a streaming chat
            completions API compatible with
            client.chat.completions.create(..., stream=True).
    """

    def __init__(self):
        self.client = OpenAI(
            api_key="lm-studio",
            base_url=get_lmstudio_url(),
        )

    async def infer_stream(
        self, model_id: str, context: list[Message]
    ) -> AsyncGenerator[TokenChunk | None, None]:
        """Asynchronously stream tokenized output from a language model completion."""

        # Convert IMessage's to OpenAI spec
        messages: list[ChatCompletionMessageParam] = [
            msg.to_openai_spec() for msg in context
        ]

        # Call the LMStudio API with streaming enabled
        response_stream = self.client.chat.completions.create(
            model=model_id,
            messages=messages,
            stream=True,
        )

        # Format and yield each token as it arrives
        for chunk in response_stream:
            stream_delta: dict[str, Any] = chunk.choices[0].delta.model_dump()
            token_chunk: TokenChunk = TokenChunk(
                content=stream_delta.get("content"),
                thought=stream_delta.get("reasoning_content"),
                # TODO: Add tool usage parsing here
            )

            # Check if the chunk is empty
            if (
                token_chunk.content is None
                and token_chunk.thought is None
                and token_chunk.tool_call is None
            ):
                break

            # Yield the token chunk
            yield token_chunk

        # Close the stream
        response_stream.close()

        # Return None to indicate the end of the stream
        yield None
