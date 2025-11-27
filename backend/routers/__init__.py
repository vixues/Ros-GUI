"""API routers."""
from .auth import router as auth_router
from .devices import router as devices_router
from .drones import router as drones_router
from .operations import router as operations_router
from .recordings import router as recordings_router
from .agent import router as agent_router
from .images import router as images_router
from .pointclouds import router as pointclouds_router

__all__ = [
    "auth_router",
    "devices_router",
    "drones_router",
    "operations_router",
    "recordings_router",
    "agent_router",
    "images_router",
    "pointclouds_router",
]

