from datetime import datetime

from models.thread import Thread
from storage.database import DataBase

DEFAULT_THREAD_TITLE: str = "New Thread"
DEFAULT_THREAD_DIR: str = "/threads"


class ThreadDBC(DataBase):
    """Database Client for managing threads."""

    def __init__(self):
        """Initialize a DB Client for managing threads."""
        super().__init__(table_name=DEFAULT_THREAD_DIR)

    def create_thread(self, title: str | None = None) -> Thread:
        """
        Create a new thread with the specified title.

        Args:
            title (str | None): The title of the thread.
                If None, a default title is used.

        Returns:
            Thread: The newly created thread object.
        """
        # Create a Thread object
        creation_time: str = datetime.now().isoformat()
        thread = Thread(
            id=self.generate_primary_key(),
            title=title or DEFAULT_THREAD_TITLE,
            created_at=creation_time,
            updated_at=creation_time,
            messages=[],
            message_count=0,
            token_count=0,
        )

        # Create a new entry for the thread
        self.create_entry(entry_name=thread.id, content=thread.model_dump_json())

        # Return the thread
        return thread

    def retrieve_thread(self, thread_id: str) -> Thread:
        """
        Retrieve a thread by its ID.

        Args:
            thread_id (str): The unique identifier of the thread to retrieve.

        Returns:
            Thread: The thread object corresponding to the given ID.

        Raises:
            EntryNotFoundError: If no entry with the specified thread_id exists.
            ValidationError: If the retrieved data cannot be validated
                as a Thread object.
        """
        thread_data = self.read_entry(entry_name=thread_id)
        return Thread.model_validate_json(thread_data)

    def update_thread(self, thread_id: str, new_title: str) -> Thread:
        """
        Update the title of an existing thread.

        Args:
            thread_id (str): The unique identifier of the thread to update.
            new_title (str): The new title to assign to the thread.

        Returns:
            Thread: The updated thread object.

        Raises:
            EntryNotFoundError: If the thread with the given ID does not exist.
        """
        thread = self.retrieve_thread(thread_id)
        thread.title = new_title
        thread.updated_at = datetime.now().isoformat()

        # Update the entry in the database
        self.replace_entry(entry_name=thread.id, content=thread.model_dump_json())
        return thread

    def delete_thread(self, thread_id: str) -> None:
        """
        Delete a thread entry from the storage.

        Args:
            thread_id (str): The unique identifier of the thread to be deleted.

        Returns:
            None
        """
        self.delete_entry(entry_name=thread_id)
