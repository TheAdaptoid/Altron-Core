from abc import ABC, abstractmethod
from typing import Any

from altron_core.core2.dtypes import Message


class IOManager(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def shape_input(self, input_data: Any) -> Message:
        """Convert the input data to a message object."""
        pass

    @abstractmethod
    def shape_output(self, output_message: Message) -> Any:
        """Convert the output data to a message object."""
        pass


class TextIOManager(IOManager):
    """A class for managing text based inputs and outputs."""

    def shape_input(self, input_data: str) -> Message:
        """Convert the input string to a message object."""
        return Message(role="user", text=input_data)

    def shape_output(self, output_message: Message) -> str:
        """Convert the output message to a string."""
        rationale: str = output_message.rationale or ""
        content: str = output_message.text or ""

        if rationale:
            return f"<thought>{rationale.strip()}</thought>\n\n{content.strip()}"
        else:
            return content.strip()


class SpeechIOManager(IOManager):
    """A class for managing speech based inputs and outputs."""

    def __init__(self):
        pass


class TextImageIOManager(IOManager):
    """A class for managing text and image based inputs and outputs."""

    def __init__(self):
        pass
