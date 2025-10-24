import os
from abc import ABC, abstractmethod

from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionMessageParam,
)

from altron_core.core3.dtypes import Message


def get_lmstudio_url() -> str:
    load_dotenv()
    host_port: str | None = os.getenv("LM_STUDIO_HOST")

    if host_port is None:
        raise ValueError("LM_STUDIO_HOST environment variable is not set.")

    return f"http://{host_port}/v1"


class InferenceEngine(ABC):
    @abstractmethod
    def infer(self, messages: list[Message]) -> list[Message]:
        pass


class LMStudio_IE(InferenceEngine):
    def __init__(self):
        self.client = OpenAI(
            api_key="lm-studio",
            base_url=get_lmstudio_url(),
        )

    def infer(self, messages: list[Message]) -> list[Message]:
        # Convert IMessage's to OpenAI spec
        spec_msgs: list[ChatCompletionMessageParam] = [
            msg.to_openai_spec() for msg in messages
        ]

        # Call the LMStudio API
        model_response: ChatCompletion = self.client.chat.completions.create(
            model="google/gemma-3-1b",
            messages=spec_msgs,
        )

        # Format and return the response as a list of IMessage
        return [Message.from_openai_spec(msg.message) for msg in model_response.choices]


class OpenAI_IE(InferenceEngine):
    def __init__(self):
        super().__init__()
