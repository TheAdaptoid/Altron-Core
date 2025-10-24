from collections.abc import AsyncGenerator
from dataclasses import asdict
from random import random

from altron_core.core3.dtypes import Message, StatePacket
from altron_core.core3.inference import InferenceEngine
from altron_core.core3.threads import load_thread, save_thread, append_to_thread


class Agent:
    def __init__(self, name: str, inference_engine: InferenceEngine):
        self.name = name
        self.inference_engine = inference_engine

    async def invoke(
        self, user_message: Message, thread_id: str
    ) -> AsyncGenerator[StatePacket, None]:
        # Perceive: process the incoming message
        thread: list[Message] = load_thread(thread_id)
        thread.append(user_message)
        working_memory: list[Message] = thread.copy()
        yield StatePacket(
            prev_state="perceiving",
            next_state="thinking",
            details={
                "message_count": len(working_memory),
                "messages": [asdict(m) for m in working_memory],
            },
        )

        # Think: analyze and decide on a response
        responses: list[Message] = self.inference_engine.infer(working_memory)
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
        for response in responses:
            thread.append(response)
            yield StatePacket(
                prev_state="responding",
                next_state="perceiving",
                details={"message": asdict(response)},
            )
        save_thread(thread_id, thread)
