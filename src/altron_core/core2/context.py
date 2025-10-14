from abc import ABC, abstractmethod

from altron_core.core2.dtypes import Message


class ContextManager(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def add_context(self, message: Message) -> None:
        pass

    @abstractmethod
    def list_context(self) -> list[Message]:
        pass


class ChatContextManager(ContextManager):
    """
    Short term, in-memory context.

    Intended for use by short-lived agents with specialized purposes.
    Utilizes in-memory message arrays.
    """

    def __init__(self, max_messages: int = 20):
        self.max_messages: int = 10
        self.chat_history: list[Message] = []

    def add_context(self, message: Message) -> None:
        if len(self.chat_history) >= self.max_messages:
            # remove oldest message
            self.chat_history.pop(0)

        # add new message
        self.chat_history.append(message)

    def list_context(self) -> list[Message]:
        return self.chat_history


class ThreadContextManager(ContextManager):
    """
    Long term, persistent context.

    Intended for use by long-lived agents and the main orchestrator.
    Utilizes JSON stored message threads.
    """

    def __init__(self, thread_id: str):
        self.thread_id: str = thread_id
        self.thread: list[Message] = []

    def fetch_thread(self) -> list[Message]:
        pass

    def save_thread(self) -> None:
        pass

    def add_context(self, message: Message) -> None:
        # load thread
        # add message
        # save thread
        pass

    def list_context(self) -> list[Message]:
        # load thread
        # return thread
        pass
