from collections.abc import Generator

from altron_core.types.chunks import ChoiceChunk
from altron_core.types.message import Message

type ChatStream = Generator[ChoiceChunk, None, str]
type InvocationStream = Generator[str, None, Message]
