import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass

import requests
from dotenv import load_dotenv

from altron_core.core2.dtypes import Message

load_dotenv()


@dataclass
class OutputBlock:
    id: str
    type: str
    content: list


class InferenceManager(ABC):
    def __init__(self, model_id: str):
        self.model_id: str = model_id

    @abstractmethod
    def infer(self, messages: list[Message]) -> Message:
        pass


class LMStudioIM(InferenceManager):
    def __init__(self, model_id: str):
        self.host: str | None = os.getenv("LM_STUDIO_HOST")
        if self.host is None:
            raise ValueError("`LM_STUDIO_HOST` environment variable not set")

        super().__init__(model_id)

    def infer(self, messages: list[Message]) -> Message:
        api_response: requests.Response = requests.post(
            url=f"http://{self.host}/v1/responses",
            json={
                "model": self.model_id,
                "input": [
                    {
                        "role": message.role,
                        "content": message.text,
                    }
                    for message in messages
                ],
                "stream": False,
            },
        )
        response_data = api_response.json()

        # debug
        with open("response_data.json", "w") as f:
            f.write(json.dumps(response_data, indent=2))

        response_msg: Message = Message(role="assistant")

        for block in response_data["output"]:
            if block["type"] == "message":
                response_msg.text = block["content"][0]["text"]
            elif block["type"] == "reasoning":
                response_msg.rationale = block["content"][0]["text"]

        return response_msg
