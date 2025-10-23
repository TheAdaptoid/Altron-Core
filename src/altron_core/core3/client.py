import asyncio
import json
from dataclasses import asdict

import websockets

from altron_core.core3.dtypes import Message


async def converse():
    uri = "ws://localhost:8000/ws"
    while True:
        async with websockets.connect(uri) as ws:
            text: str = input("You >>> ")

            # Quit if the user types 'exit' or 'quit'
            if text.lower() in {"exit", "quit"}:
                print("Exiting...")
                await ws.close()
                return

            # Send the message to the server
            message = Message(text=text, role="user")
            await ws.send(json.dumps(asdict(message)))

            # Listen for responses until the connection is closed
            while True:
                try:
                    response = await ws.recv()
                    print(f"Altron >>> {response}\n", end="", flush=True)

                except websockets.ConnectionClosed:
                    print("\n\033[31m[[End of Line]]\033[0m\n")
                    break


if __name__ == "__main__":
    asyncio.run(converse())
