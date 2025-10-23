import json
from dataclasses import asdict

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, WebSocketException

from altron_core.core3.agent import Agent
from altron_core.core3.dtypes import Message

app = FastAPI()


@app.websocket("/ws")
async def converse(websocket: WebSocket):
    await websocket.accept()

    try:
        msg_json: str = await websocket.receive_text()
        msg_dict = json.loads(msg_json)
        msg_obj = Message(**msg_dict)

        agent = Agent(name="WebSocket Agent")

        async for state in agent.invoke(msg_obj):
            text = json.dumps(asdict(state))
            print(f"Sending state: {text}")
            await websocket.send_text(text)

            if state.prev_state in {"responding", "failed"}:
                # Close the connection after responding or failing
                await websocket.close()

    except WebSocketDisconnect:
        await websocket.close()

    except WebSocketException:
        await websocket.close()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
