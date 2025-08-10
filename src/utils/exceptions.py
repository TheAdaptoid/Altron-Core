class TableNotFoundError(Exception):
    """Exception raised when a DB table is not found."""

    def __init__(self, table_name: str) -> None:
        super().__init__(f"Table not found: {table_name}")


class EntryNotFoundError(Exception):
    """Exception raised when a DB entry is not found."""

    def __init__(self, entry_id: str) -> None:
        super().__init__(f"Entry not found: {entry_id}")


class ThreadNotFoundError(Exception):
    """Exception raised when a conversation thread is not found."""

    def __init__(self, thread_id: str) -> None:
        super().__init__(f"Conversation thread not found: {thread_id}")
