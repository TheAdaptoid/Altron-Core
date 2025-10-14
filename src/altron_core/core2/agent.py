from typing import Any

from altron_core.core2.context import ChatContextManager, ContextManager
from altron_core.core2.dtypes import Message
from altron_core.core2.inference import InferenceManager, LMStudioIM
from altron_core.core2.io import IOManager, TextIOManager


class ToolManager:
    def __init__(self):
        pass


class MemoryManager:
    def __init__(self):
        pass


class Agent:
    def __init__(
        self,
        inference_manager: InferenceManager,
        io_manager: IOManager = TextIOManager(),
        context_manager: ContextManager = ChatContextManager(),
    ) -> None:
        self.inference_manager: InferenceManager = inference_manager
        self.io_manager: IOManager = io_manager
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


def main() -> None:
    test_agent = Agent(LMStudioIM(model_id="qwen/qwen3-4b-thinking-2507"))
    while True:
        user_input = str(input("User >>> "))
        if user_input == "exit":
            break
        response: str = test_agent.invoke(user_input)
        print(f"Altron >>> {response}")


if __name__ == "__main__":
    main()
