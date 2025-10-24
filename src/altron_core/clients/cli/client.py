import asyncio
import json
from dataclasses import asdict

import requests
import websockets

from altron_core.types.dtypes import ConversePacket, Message, MessageThread


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


async def converse(user_message: Message, thread_id: str) -> None:
    conv_pack: ConversePacket = ConversePacket(
        thread_id=thread_id, message=user_message
    )
    conv_pack_text: str = json.dumps(asdict(conv_pack))
    uri = "ws://localhost:8000/ws"

    # Connect to the WebSocket server
    async with websockets.connect(uri) as ws:
        await ws.send(conv_pack_text)

        # Listen for responses until the connection is closed
        while True:
            try:
                response = await ws.recv()
                print(
                    f"Altron >>> {json.dumps(json.loads(response), indent=2)}\n",
                    end="",
                    flush=True,
                )

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
        user_input: str = input("User >>> ")
        if user_input == "exit":
            break

        user_msg: Message = Message(text=user_input, role="user")
        await converse(user_message=user_msg, thread_id=thread_id)

    # Delete the thread
    await delete_thread(thread_id)


if __name__ == "__main__":
    asyncio.run(main())
