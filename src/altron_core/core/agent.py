from collections.abc import AsyncGenerator

from altron_core.core.inference import InferenceEngine
from altron_core.core.threads import create_thread, load_thread, save_thread
from altron_core.types.dtypes import (
    Message,
    StreamStatePacket,
    ThreadId,
)


class Agent:
    def __init__(self, name: str, model_id: str, inference_engine: InferenceEngine):
        self._name: str = name
        self._model: str = model_id
        self._engine: InferenceEngine = inference_engine

    def _create_working_memory(
        self, thread_id: str | None, user_message: Message
    ) -> tuple[ThreadId, list[Message]]:
        """
        Create working memory for the agent to reason with.

        If thread_id is None, create a new thread. Otherwise, load the existing thread
        and append the user message to the thread's message list. Finally, save the
        thread and return the thread ID and the list of messages.

        Parameters
        ----------
        thread_id : str | None
            ID of the thread to load/create. If None, a new thread is created.
        user_message : Message
            The message from the user to add to the thread's working memory.

        Returns
        -------
        tuple[ThreadId, list[Message]]
            A tuple containing the thread ID and the list of messages in the working memory.
        """
        # If thread_id is None,
        # create a new thread
        if thread_id is None:
            thread = create_thread()

        # Otherwise, load the existing thread
        else:
            thread = load_thread(thread_id)

        # Add user message to thread
        thread.messages.append(user_message)
        save_thread(thread)

        # TODO: Conduct RAG here to augment working memory

        return thread.id, thread.messages

    def _save_final_response(self, thread_id: str, agent_message: Message) -> None:
        """
        Persist the agent's final message to a conversation thread.

        This internal helper loads a thread by ID, appends the provided Message
        instance to the thread's messages list, and persists the updated thread.

        Parameters
        ----------
        thread_id : str
            Identifier of the thread to update.
        agent_message : Message
            The agent's message to append and save.

        Raises
        ------
        Exception
            If loading the thread, appending the message, or saving the thread fails,
            a generic Exception is raised indicating the save operation failed.
        """
        try:
            thread = load_thread(thread_id)
            thread.messages.append(agent_message)
            save_thread(thread)
        except Exception:
            raise Exception("Failed to save final response to thread.")

    async def invoke(
        self, user_message: Message, thread_id: str | None = None
    ) -> AsyncGenerator[StreamStatePacket, None]:
        """
        Invoke the agent to process a user message and produce a streamed response.

        This asynchronous generator implements a multi-stage pipeline and yields
        StreamStatePacket instances to communicate progress, intermediate tokens,
        errors, and the final result.

        Stages and yielded semantics:
        - "perceiving"
            - Emitted immediately to indicate the incoming message is being processed.
            - Creates or resumes a thread and builds the working memory
            from the provided user message.

        - "thinking"
            - Emitted to indicate the model/engine is producing internal "thought" tokens.
            - The function obtains a streaming inference from the agent engine (via self._engine.infer_stream)
              and iterates the stream for thought tokens. Thought tokens are expected to be tokens whose
              content field is absent/None and whose thought field carries intermediate reasoning. Each
              yielded StreamStatePacket during this stage has curr_state="thinking" and, when active,
              stream="active" with token set to the thought string.

        - "responding"
            - Emitted to indicate the model is emitting the final response content.
            - The function continues consuming the same stream for content tokens (tokens with non-None
              content), accumulates them into a response buffer, and yields StreamStatePacket instances
              with curr_state="responding", stream="active", and token set to the emitted content fragment.

        - Saving the final response
            - After streaming completes, the accumulated response is wrapped in a Message with role="agent"
              and saved to the thread via self._save_final_response(thread_id, agent_message).
            - If saving fails, the generator yields a StreamStatePacket with curr_state="failed" and an
              error string describing the failure.

        - "done"
            - Emitted as the final state after any cleanup/save handling to indicate the operation finished.

        Parameters
        ----------
        - user_message (Message): the incoming user message to process.
        - thread_id (str | None): optional identifier of the thread to resume; when None a new thread is created.

        Returns
        -------
        - AsyncGenerator[StreamStatePacket, None]: an async generator that yields StreamStatePacket values
          describing progress, intermediate tokens, errors, and completion. Consumers should iterate the
          generator to receive both intermediate "thinking" and "responding" tokens and the final states.

        Notes and side effects:
        - This function interacts with internal components: self._create_working_memory, self._engine.infer_stream,
          and self._save_final_response.
        - The stream produced by the engine is expected to emit two logical phases: internal thought tokens
          (no content, present as thought) followed by content tokens (non-empty content fragments). The
          generator relies on that convention to separate thinking vs responding yields.
        - The save error is caught and reported via a "failed" packet; other exceptions raised during
          perception or inference are not explicitly caught here and will propagate to the caller unless
          handled externally.
        - Consumers should handle StreamStatePacket values and inspect fields such as curr_state, stream,
          token, and error to drive UI updates or further processing.
        """
        # Perceive: process the incoming message
        yield StreamStatePacket(curr_state="perceiving")
        thread_id, working_memory = self._create_working_memory(thread_id, user_message)

        # Think: analyze and decide on a response
        yield StreamStatePacket(curr_state="thinking")
        stream = self._engine.infer_stream(model_id=self._model, context=working_memory)
        async for token in stream:
            # Check if the thought stream has ended
            if token is None or token.content is not None:
                break

            # Otherwise, yield the thought token
            yield StreamStatePacket(
                curr_state="thinking", stream="active", token=token.thought
            )

        # Act: execute tools if necessary
        # NOTE: Skipped for now

        # Respond: generate the final response
        yield StreamStatePacket(curr_state="responding")
        buffer: str = ""
        async for token in stream:
            # Check if the stream has ended
            if token is None or token.content is None:
                break

            # Yield the content token
            buffer += token.content
            yield StreamStatePacket(
                curr_state="responding", stream="active", token=token.content
            )

        # Finalize: save the updated thread
        agent_message: Message = Message(text=buffer, role="agent")
        try:
            self._save_final_response(thread_id, agent_message)
        except Exception as e:
            yield StreamStatePacket(
                curr_state="failed",
                error=f"Error saving response: {str(e)}",
            )

        # Finally, yield inactive state
        yield StreamStatePacket(curr_state="done")
