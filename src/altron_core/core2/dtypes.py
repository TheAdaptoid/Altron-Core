from dataclasses import dataclass, field
from typing import Literal


@dataclass
class Message:
    text: str | None = None
    rationale: str | None = None
    role: Literal["user", "assistant", "system", "tool"] = field(default="user")
