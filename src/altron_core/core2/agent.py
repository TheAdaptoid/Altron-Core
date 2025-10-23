import asyncio
from typing import Any

from altron_core.core2.context import ChatContextManager, ContextManager
from altron_core.core2.dtypes import Message
from altron_core.core2.inference import InferenceManager, LMStudioIM
from altron_core.core2.io import IOManager


class MemoryManager:
    def __init__(self):
        pass


class Agent:
    def __init__(
        self,
        inference_manager: InferenceManager,
        context_manager: ContextManager = ChatContextManager(),
    ) -> None:
        self.inference_manager: InferenceManager = inference_manager
        self.io_manager: IOManager = IOManager()
        self.context_manager: ContextManager = context_manager

    def _perceive(self, input_data: Any) -> Message:
        """Perceive the input data and return a message object."""
        return self.io_manager.shape_input(input_data)

    def _reason(self, context: list[Message]) -> Message:
        """Reason about the context and return a message object."""
        return self.inference_manager.infer(self.context_manager.list_context())

    def act(self):
        pass

    def _respond(self, message: Message) -> Any:
        """Respond to the user."""
        return self.io_manager.shape_output(message)

    def invoke(self, input_data: Any) -> Any:
        # Perceive the user's input
        perception: Message = self._perceive(input_data)

        # Update context
        self.context_manager.add_context(message=perception)

        # Create copy of the context to be used
        # for reasoning and tool calling
        working_memory: list[Message] = self.context_manager.list_context()
        response = self._reason(context=working_memory)
        self.context_manager.add_context(message=response)
        working_memory.append(response)

        # Formulate a response
        return self._respond(response)

    async def _invoke(self, user_msg: Message) -> Message:
        # Add the user message to working memory
        working_memory: list[Message] = self.context_manager.list_context()
        working_memory.append(user_msg)

        # Process the user message
        init_response: Message = await asyncio.to_thread(
            self.inference_manager.infer, working_memory
        )

        # Handle tools if needed
        # TODO: implement tool handling

        # Update context with the response
        self.context_manager.add_context(message=user_msg)
        self.context_manager.add_context(message=init_response)

        # Return the response message
        return init_response

    async def text_invoke(self, input: str) -> str | tuple[str, str]:
        # convert the string into a message object
        user_msg: Message = self.io_manager.string_to_message(string=input)

        # invoke the agent asynchronously
        response_msg: Message = await self._invoke(user_msg)

        # return the response as a string)
        return self.io_manager.message_to_string(response_msg)

    async def speech_invoke(self, input: bytes) -> bytes: ...  # To be implemented

    async def image_invoke(
        self, input: list[bytes], context: str
    ) -> str: ...  # To be implemented


async def main() -> None:
    test_agent = Agent(LMStudioIM(model_id="qwen/qwen3-4b-thinking-2507"))
    while True:
        user_input = str(input("User >>> "))
        if user_input == "exit":
            break
        response: str | tuple[str, str] = await test_agent.text_invoke(user_input)

        print(f"Altron {'=' * 20}")
        if isinstance(response, tuple):
            print(f"<rationale>\n{response[0]}\n</rationale>\n")
            print(f"{response[1]}")
        else:
            print(f"{response}")


if __name__ == "__main__":
    asyncio.run(main())
