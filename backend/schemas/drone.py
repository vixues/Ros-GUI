"""Drone schemas."""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from ..models.drone import DroneStatus


class DroneCreate(BaseModel):
    """Drone creation request model."""
    name: str = Field(..., min_length=1, max_length=100, description="Drone name")
    drone_id: str = Field(..., min_length=1, max_length=50, description="Unique drone identifier")
    device_id: Optional[int] = Field(None, description="Associated device ID")
    connection_url: Optional[str] = Field(None, max_length=255, description="ROS bridge URL")
    use_mock: bool = Field(default=False, description="Use mock client")
    mock_config: Optional[Dict[str, Any]] = Field(None, description="Mock client configuration")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class DroneUpdate(BaseModel):
    """Drone update request model."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Drone name")
    device_id: Optional[int] = Field(None, description="Associated device ID")
    connection_url: Optional[str] = Field(None, max_length=255, description="ROS bridge URL")
    use_mock: Optional[bool] = Field(None, description="Use mock client")
    mock_config: Optional[Dict[str, Any]] = Field(None, description="Mock client configuration")
    status: Optional[str] = Field(None, description="Drone status")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class DroneConnectionRequest(BaseModel):
    """Drone connection request model."""
    connection_url: str = Field(..., description="ROS bridge URL")
    use_mock: bool = Field(default=False, description="Use mock client")
    mock_config: Optional[Dict[str, Any]] = Field(None, description="Mock client configuration")


class DroneStateSnapshot(BaseModel):
    """Drone state snapshot model."""
    is_connected: bool
    is_armed: bool
    mode: Optional[str]
    battery: float
    latitude: Optional[float]
    longitude: Optional[float]
    altitude: Optional[float]
    roll: Optional[float]
    pitch: Optional[float]
    yaw: Optional[float]
    landed: bool
    reached: bool
    returned: bool
    tookoff: bool
    last_state_update: Optional[datetime]


class DroneResponse(BaseModel):
    """Drone response model."""
    id: int
    name: str
    drone_id: str
    device_id: Optional[int]
    status: str
    is_connected: bool
    is_armed: bool
    mode: Optional[str]
    battery: float
    latitude: Optional[float]
    longitude: Optional[float]
    altitude: Optional[float]
    roll: Optional[float]
    pitch: Optional[float]
    yaw: Optional[float]
    landed: bool
    reached: bool
    returned: bool
    tookoff: bool
    connection_url: Optional[str]
    use_mock: bool
    last_state_update: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DroneStatusResponse(BaseModel):
    """Drone status response model."""
    drone_id: int
    name: str
    status: str
    is_connected: bool
    state: DroneStateSnapshot
    
    class Config:
        from_attributes = True

