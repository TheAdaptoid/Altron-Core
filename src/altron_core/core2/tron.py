from dataclasses import dataclass


@dataclass
class IdendityCard:
    name: str
    purpose: str
    personality: str | None = None
