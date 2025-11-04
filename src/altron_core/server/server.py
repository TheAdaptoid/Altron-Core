import json
from dataclasses import asdict
from typing import Any

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, WebSocketException

from altron_core.core.agent import Agent
from altron_core.core.inference import LMStudio_IE
from altron_core.core.threads import create_thread, load_thread, remove_thread
from altron_core.types.dtypes import ConversePacket

app = FastAPI()


@app.post("/thread")
async def create_new_thread(title: str | None = None) -> dict[str, Any]:
    """
    Endpoint for creating new message threads.

    Args:
        title (str | None, optional):
            The title of the new thread. Defaults to None.

    Returns:
        dict[str, Any]: The details of the newly created thread.
    """
    return asdict(create_thread(title=title))


@app.get("/thread/{thread_id}")
async def read_thread(thread_id: str) -> dict[str, Any]:
    """
    Endpoint for reading a message thread.

    Args:
        thread_id (str): The ID of the thread to read.

    Returns:
        dict[str, Any]: The details of the thread.
    """
    return asdict(load_thread(thread_id))


@app.patch("/thread/{thread_id}")
async def update_thread(thread_id: str, new_title: str) -> dict[str, Any]:
    """
    Endpoint for updating a message thread.

    Args:
        thread_id (str): The ID of the thread to update.
        new_title (str): The new title for the thread.

    Returns:
        dict[str, Any]: The details of the updated thread.
    """
    raise NotImplementedError


@app.delete("/thread/{thread_id}")
async def delete_thread(thread_id: str) -> dict[str, str | bool]:
    """
    Endpoint for deleting a message thread.

    Args:
        thread_id (str): The ID of the thread to delete.

    Returns:
        dict[str, str | bool]: The details of the deleted thread.
    """
    try:
        remove_thread(thread_id)
    except Exception as e:
        return {
            "id": thread_id,
            "deleted": False,
            "error": str(e),
        }
    return {
        "id": thread_id,
        "deleted": True,
    }


@app.websocket("/ws")
async def converse(websocket: WebSocket):
    await websocket.accept()
    connected: bool = True

    try:
        # Parse the incoming packet
        conv_pack_json: str = await websocket.receive_text()
        conv_pack_dict = json.loads(conv_pack_json)
        conv_pack_obj = ConversePacket.from_dict(conv_pack_dict)

        # Spin up the agent
        agent = Agent(
            name="WebSocket Agent",
            model_id="qwen/qwen3-4b-thinking-2507",
            inference_engine=LMStudio_IE(),
        )

        # Invoke the agent
        async for state in agent.invoke(
            user_message=conv_pack_obj.message, thread_id=conv_pack_obj.thread_id
        ):
            state_text: str = json.dumps(asdict(state))
            print(f"Sending state: {state_text}")

            try:
                await websocket.send_text(state_text)
            except (WebSocketDisconnect, WebSocketException, RuntimeError) as e:
                print(f"Stopping Stream. Websocket error during send: {e}")
                connected = False
                return
            except Exception as e:
                print(f"Stopping Stream. Unexpected error during send: {e}")
                connected = False
                return

            if state.curr_state == "done":
                break

        print("Conversation ended successfully.")
    except WebSocketException as e:
        print(f"WebSocket exception occurred while receiving/handling: {e}")
        connected = False
    except Exception as e:
        print(f"Unhandled exception in converse handler: {e}")
        connected = False
    finally:
        # only attempt a graceful close if we
        # believe the client is still connected
        if connected:
            try:
                await websocket.close()
            except RuntimeError:
                # If close already sent or connection lost, ignore
                pass


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
