from typing import cast

from altron_core.core.agent import Agent, AgentRole
from altron_core.types import Message

RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"
RESET = "\033[0m"

# Color codes
C_USER = GREEN
C_AGENT = BLUE
C_WARNING = YELLOW
C_ERROR = RED


def get_user_input() -> Message:
    print(f"{C_USER}User >>>{RESET} ", end="")
    content: str = input()
    handle_commands(content)
    return Message(role="user", content=content)


def handle_commands(command: str) -> None:
    match command.lower():
        case "exit":
            raise SystemExit(f"{C_WARNING}Exiting Altron CLI.{RESET}")
        case _:
            return


def get_agent_response(thread: list[Message]) -> Message:
    agent = Agent(role=AgentRole.GENERALIST)
    response_stream = agent.invoke(thread)

    # Prepare for streaming response
    print(f"{C_AGENT}Altron >>>{RESET} ", end="")
    code_mode: bool = False
    color: str = WHITE

    # Stream the response
    while True:
        try:
            token: str = next(response_stream)

            if "`" in token:
                code_mode = not code_mode
                color = CYAN if code_mode else WHITE

            print(f"{color}{token}{RESET}", end="", flush=True)
        except StopIteration as e:
            # Return the final message
            return cast(Message, e.value)


def main() -> None:
    thread: list[Message] = []
    while True:
        thread.append(get_user_input())
        thread.append(get_agent_response(thread))


if __name__ == "__main__":
    main()
