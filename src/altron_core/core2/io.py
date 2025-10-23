from typing import Literal

from altron_core.core2.dtypes import Message

EMPTY_TEXT: str = "[No Text Content]"


class IOManager:
    def __init__(self):
        pass

    def string_to_message(
        self, string: str, role: Literal["user", "assistant", "system", "tool"] = "user"
    ) -> Message:
        """Convert a string to a message object."""
        return Message(role=role, text=string)

    def message_to_string(self, message: Message) -> str | tuple[str, str]:
        """
        Convert a message object to a string.

        If the message has a rationale, return a tuple of the rationale
        and the message text. Otherwise, return the message text.

        Args:
            message (Message): The message object to convert.

        Returns:
            str | tuple[str, str]: The converted string or
                tuple of rationale and message text.
        """
        message_text: str = message.text or EMPTY_TEXT
        if message.rationale:
            return message.rationale.strip(), message_text.strip()
        else:
            return message_text.strip()
