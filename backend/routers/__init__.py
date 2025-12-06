"""API routers."""
from .auth import router as auth_router
from .devices import router as devices_router
from .drones import router as drones_router
from .operations import router as operations_router
from .recordings import router as recordings_router
from .agent import router as agent_router
from .images import router as images_router
from .pointclouds import router as pointclouds_router
from .tasks import router as tasks_router
from .logs import router as logs_router
from .health import router as health_router

__all__ = [
    "auth_router",
    "devices_router",
    "drones_router",
    "operations_router",
    "recordings_router",
    "agent_router",
    "images_router",
    "pointclouds_router",
    "tasks_router",
    "logs_router",
    "health_router",
]

