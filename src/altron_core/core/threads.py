import json
import os
from dataclasses import asdict
from time import time_ns

from altron_core.types.dtypes import MessageThread

THREAD_STORE: str = "./src/altron_core/threads"
DEFAULT_THREAD_TITLE: str = "New Thread"


def _thread_path_builder(thread_id: str) -> str:
    return f"{THREAD_STORE}/{thread_id}.json"


def create_thread(title: str | None = None) -> MessageThread:
    """
    Create a new message thread.

    Args:
        title (str, optional): The title of the message thread.

    Returns:
        str: The ID of the created message thread.

    Raises:
        ValueError: If a thread with the same ID already exists.
        RuntimeError: If the thread file creation fails.
    """
    # Use current time in nanoseconds as a simple unique thread ID
    thread_id: str = str(time_ns())

    # Create the thread
    if title is None:
        title = DEFAULT_THREAD_TITLE
    thread = MessageThread(id=thread_id, title=title)

    # Attempt to create the thread file
    try:
        file_path: str = _thread_path_builder(thread_id)
        with open(file_path, "x") as file:
            json.dump(asdict(thread), file, indent=4)
    except FileExistsError:
        raise ValueError(f"Thread with ID {thread.id} already exists.")
    except Exception as e:
        raise RuntimeError(f"Failed to create thread file for ID {thread.id}: {e}")

    return thread


def load_thread(thread_id: str) -> MessageThread:
    """
    Load a message thread from a file.

    Args:
        thread_id (str): The ID of the message thread to load.

    Returns:
        MessageThread: The loaded message thread.

    Raises:
        ValueError: If the thread file does not exist or is not a valid JSON file.
        RuntimeError: If the thread file loading fails.
    """
    try:
        file_path: str = _thread_path_builder(thread_id)
        with open(file_path, "r") as file:
            thread_data = json.load(file)
            thread_obj = MessageThread.from_dict(thread_data)
            return thread_obj
    except FileNotFoundError:
        raise ValueError(f"Thread with ID {thread_id} does not exist.")
    except json.JSONDecodeError:
        raise ValueError(f"Thread with ID {thread_id} is not a valid JSON file.")
    except Exception as e:
        raise RuntimeError(f"Failed to load thread file for ID {thread_id}: {e}")


def save_thread(thread: MessageThread) -> None:
    """
    Save a message thread to a file.

    Args:
        thread (MessageThread): The message thread to save.

    Raises:
        ValueError: If the thread file does not exist.
        RuntimeError: If the thread file saving fails.
    """
    try:
        file_path: str = _thread_path_builder(thread.id)
        with open(file_path, "w") as file:
            json.dump(asdict(thread), file, indent=4)
    except FileNotFoundError:
        raise ValueError(f"Thread with ID {thread.id} does not exist.")
    except Exception as e:
        raise RuntimeError(f"Failed to save thread file for ID {thread.id}: {e}")


def rename_thread(thread_id: str, new_title: str) -> None:
    raise NotImplementedError


def remove_thread(thread_id: str) -> None:
    """
    Remove a message thread from storage.

    Args:
        thread_id (str): The ID of the message thread to remove.

    Raises:
        ValueError: If the thread file does not exist.
        RuntimeError: If the thread file deletion fails.
    """
    try:
        file_path: str = _thread_path_builder(thread_id)
        os.remove(file_path)
    except FileNotFoundError:
        raise ValueError(f"Thread with ID {thread_id} does not exist.")
    except Exception as e:
        raise RuntimeError(f"Failed to delete thread file for ID {thread_id}: {e}")
