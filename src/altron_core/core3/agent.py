from collections.abc import AsyncGenerator
from dataclasses import asdict

from altron_core.core3.dtypes import Message, MessageThread, StatePacket
from altron_core.core3.inference import InferenceEngine
from altron_core.core3.threads import load_thread, save_thread


class Agent:
    def __init__(self, name: str, model_id: str, inference_engine: InferenceEngine):
        self._name: str = name
        self._model: str = model_id
        self._engine: InferenceEngine = inference_engine

    async def invoke(
        self, user_message: Message, thread_id: str
    ) -> AsyncGenerator[StatePacket, None]:
        # Perceive: process the incoming message
        try:
            thread: MessageThread = load_thread(thread_id)
        except Exception as e:
            yield StatePacket(
                prev_state="failed",
                next_state="perceiving",
                details={"error": str(e)},
            )
            raise e
        thread.messages.append(user_message)  # Add user msg to thread
        working_memory: list[Message] = thread.messages
        yield StatePacket(
            prev_state="perceiving",
            next_state="thinking",
            details={
                "thread_id": thread.id,
                "thread_title": thread.title,
                "message_count": len(working_memory),
                "messages": [asdict(m) for m in working_memory],
            },
        )

        # Think: analyze and decide on a response
        responses: list[Message] = self._engine.infer(
            model_id=self._model, messages=working_memory
        )
        yield StatePacket(
            prev_state="thinking",
            next_state="responding",
            details={"rationale": "[[Any Reasoning Tokens Generated]]"},
        )

        # Act: execute tools if necessary
        # yield StatePacket(
        #     prev_state="acting",
        #     next_state="responding",
        # )

        # Respond: generate the final response
        for agent_message in responses:
            # Add final responses to the thread
            thread.messages.append(agent_message)
            yield StatePacket(
                prev_state="responding",
                next_state="perceiving",
                details={"message": asdict(agent_message)},
            )
        # Save the updated thread
        try:
            save_thread(thread)
        except Exception as e:
            yield StatePacket(
                prev_state="failed",
                next_state="perceiving",
                details={"error": str(e)},
            )
            raise e
