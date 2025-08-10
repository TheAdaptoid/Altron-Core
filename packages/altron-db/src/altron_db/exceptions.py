class EntryNotFoundError(Exception):
    """Exception raised when a DB entry is not found."""

    def __init__(self, entry_id: str) -> None:
        super().__init__(f"Entry not found: {entry_id}")
