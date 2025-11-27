"""Pydantic schemas for API requests and responses."""
from .response import ResponseModel, ErrorResponse
from .auth import Token, TokenData, UserCreate, UserResponse, UserLogin
from .device import DeviceCreate, DeviceUpdate, DeviceResponse
from .drone import (
    DroneCreate,
    DroneUpdate,
    DroneResponse,
    DroneStatusResponse,
    DroneConnectionRequest,
    DroneStateSnapshot
)
from .operation import OperationCreate, OperationResponse, OperationQuery
from .recording import RecordingCreate, RecordingUpdate, RecordingResponse
from .agent import (
    AgentSessionCreate,
    AgentSessionResponse,
    AgentActionRequest,
    AgentActionResponse,
    AgentMessage
)

__all__ = [
    "ResponseModel",
    "ErrorResponse",
    "Token",
    "TokenData",
    "UserCreate",
    "UserResponse",
    "UserLogin",
    "DeviceCreate",
    "DeviceUpdate",
    "DeviceResponse",
    "DroneCreate",
    "DroneUpdate",
    "DroneResponse",
    "DroneStatusResponse",
    "DroneConnectionRequest",
    "DroneStateSnapshot",
    "OperationCreate",
    "OperationResponse",
    "OperationQuery",
    "RecordingCreate",
    "RecordingUpdate",
    "RecordingResponse",
    "AgentSessionCreate",
    "AgentSessionResponse",
    "AgentActionRequest",
    "AgentActionResponse",
    "AgentMessage",
]

