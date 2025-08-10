import os
import uuid

from altron_db.exceptions import EntryNotFoundError

DEFAULT_DB_DIR: str = "../database"


class DataBase:
    def __init__(self, table_name: str):
        self._table_name: str = table_name
        self._table_path: str = os.path.join(self._get_db_path(), f"{table_name}/")
        os.makedirs(self._table_path, exist_ok=True)

    def _get_db_path(self) -> str:
        return os.getenv("DB_PATH", DEFAULT_DB_DIR)

    def _validate_entry(self, entry_path: str) -> None:
        """
        Validate that the entry exists.

        Args:
            entry_path (str): The path to the entry to validate.

        Raises:
            EntryNotFoundError: If the entry does not exist.
        """
        if not os.path.exists(entry_path):
            raise EntryNotFoundError(entry_path)

    def create_entry(self, entry_name: str, content: str) -> None:
        """
        Create a new file with the given content.

        Args:
            entry_name (str): The name of the entry to create.
            content (str): The content to write to the file.

        Raises:
            FileExistsError: If the file already exists.
        """
        full_path: str = os.path.join(self._table_path, entry_name)
        if os.path.exists(full_path):
            raise FileExistsError(f"Entry already exists: {entry_name}")
        with open(full_path, "w") as f:
            f.write(content)

    def read_entry(self, entry_name: str) -> str:
        """
        Read the content of a file.

        Args:
            entry_name (str): The name of the entry to read.

        Returns:
            str: The content of the entry.
        """
        self._validate_entry(entry_name)
        with open(entry_name, "r") as f:
            return f.read()

    def replace_entry(self, entry_name: str, content: str) -> None:
        """
        Replace the content of an entry.

        Args:
            entry_name (str): The name of the entry to replace.
            content (str): The new content to write to the entry.
        """
        self._validate_entry(entry_name)
        with open(entry_name, "w") as f:
            f.write(content)

    def delete_entry(self, entry_name: str) -> None:
        """
        Delete an entry.

        Args:
            entry_name (str): The name of the entry to delete.
        """
        self._validate_entry(entry_name)
        os.remove(entry_name)

    def generate_primary_key(self) -> str:
        """
        Generate a unique ID.

        Returns:
            str: The generated unique ID.
        """
        return str(uuid.uuid4())
