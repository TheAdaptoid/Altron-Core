from fastapi import FastAPI

app = FastAPI()


@app.post("/chat")
async def chat_endpoint(message: str):
    return {"message": message}
