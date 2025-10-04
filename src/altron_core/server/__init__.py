from src.altron_core.server.discord import router as discord_router
from src.altron_core.server.general import router as general_router
from src.altron_core.server.subprocess import router as subprocess_router

__all__ = [
    "discord_router",
    "general_router",
    "subprocess_router",
]
