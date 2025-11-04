import asyncio
import json
from dataclasses import asdict
from datetime import datetime
from typing import Literal

import requests
import websockets

from altron_core.types.dtypes import (
    ConversePacket,
    Message,
    MessageThread,
    StreamStatePacket,
)

# Colors for terminal output
RESET_COLOR = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"


async def init_thread() -> str:
    url = "http://localhost:8000/thread"
    response = requests.post(url, json={"title": "Test Thread"})
    thread_id = response.json()["id"]
    return thread_id


async def read_thread(thread_id: str) -> MessageThread:
    url = f"http://localhost:8000/thread/{thread_id}"
    response = requests.get(url)
    return MessageThread(**response.json())


async def delete_thread(thread_id: str) -> None:
    url = f"http://localhost:8000/thread/{thread_id}"
    requests.delete(url)


def display_user_msg() -> Message:
    print(f"{YELLOW}User\t{RESET_COLOR}[{datetime.now().strftime('%H:%M:%S')}]")
    user_input = input(f"{YELLOW}$ {RESET_COLOR}")
    return Message(text=user_input, role="user")


def display_agent_msg_header() -> None:
    print(f"{BLUE}Agent\t{RESET_COLOR}[{datetime.now().strftime('%H:%M:%S')}]")


def display_agent_msg_body(token: str) -> None:
    print(f"{token}", end="", flush=True)


async def converse(user_message: Message, thread_id: str) -> None:
    conv_pack: ConversePacket = ConversePacket(
        thread_id=thread_id, message=user_message
    )
    conv_pack_text: str = json.dumps(asdict(conv_pack))
    uri = "ws://localhost:8000/ws"

    # Connect to the WebSocket server
    async with websockets.connect(uri, ping_interval=10, ping_timeout=20) as ws:
        await ws.send(conv_pack_text)
        mode: Literal["thinking", "responding", "done"] = "done"
        display_agent_msg_header()

        # Listen for responses until the connection is closed
        while True:
            try:
                response = await ws.recv()
                packet = StreamStatePacket(**json.loads(response))
                if packet.curr_state == "thinking" and mode != "thinking":
                    print(f"{BLUE}")
                    mode = "thinking"
                elif packet.curr_state == "responding" and mode != "responding":
                    print(f"{GREEN}{'=' * 50}\n> {RESET_COLOR}", end="", flush=True)
                    mode = "responding"

                if packet.stream == "active" and packet.token:
                    _token = packet.token
                    if _token.startswith("\n") and mode == "thinking":
                        _token = _token.lstrip("\n")
                    display_agent_msg_body(_token)

            except websockets.ConnectionClosed:
                print("\n\033[31m[[End of Line]]\033[0m\n")
                break


async def main() -> None:
    thread_id = await init_thread()
    thread_obj: MessageThread = await read_thread(thread_id)

    # Display the thread
    for msg in thread_obj.messages:
        print(f"{msg.role} >>> {msg.text}")

    # Start the conversation
    while True:
        user_msg: Message = display_user_msg()

        if user_msg.text == "exit":
            break

        await converse(user_message=user_msg, thread_id=thread_id)

    # Delete the thread
    await delete_thread(thread_id)


if __name__ == "__main__":
    asyncio.run(main())
