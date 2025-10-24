import json

from altron_core.core3.dtypes import Message

THREAD_STORE: str = "./src/altron_core/threads"


def load_thread(thread_id: str) -> list[Message]:
    file_path: str = f"{THREAD_STORE}/{thread_id}.json"

    try:
        with open(file_path, "r") as file:
            messages_data = json.load(file)
            return [Message(**msg) for msg in messages_data]
    except FileNotFoundError:
        raise ValueError(f"Thread with ID {thread_id} does not exist.")


def save_thread(thread_id: str, messages: list[Message]) -> None:
    file_path: str = f"{THREAD_STORE}/{thread_id}.json"
    with open(file_path, "w") as file:
        json.dump([msg.__dict__ for msg in messages], file, indent=4)


def append_to_thread(thread_id: str, message: Message) -> None:
    messages = load_thread(thread_id)
    messages.append(message)
    save_thread(thread_id, messages)
