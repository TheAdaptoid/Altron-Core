from collections.abc import AsyncGenerator
from dataclasses import asdict
from random import random

from altron_core.core3.dtypes import Message, StatePacket


class Agent:
    def __init__(self, name):
        self.name = name

    async def invoke(self, message: Message) -> AsyncGenerator[StatePacket, None]:
        # Perceive: process the incoming message
        yield StatePacket(
            prev_state="perceiving",
            next_state="thinking",
        )

        # Think: analyze and decide on a response
        yield StatePacket(
            prev_state="thinking",
            next_state="acting",
            details={"rationale": "[[Any Reasoning Tokens Generated]]"},
        )

        # Act: execute tools if necessary
        if random() < 0.3:  # 30% chance to simulate tool use
            yield StatePacket(
                prev_state="acting",
                next_state="responding",
            )
            yield StatePacket(
                prev_state="acting",
                next_state="responding",
            )

        # Respond: generate the final response
        yield StatePacket(
            prev_state="responding",
            next_state="perceiving",
            details={
                "message": asdict(
                    Message(text="This is a response from the agent.", role="agent")
                )
            },
        )
