"""Device schemas."""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from ..models.device import DeviceType


class DeviceCreate(BaseModel):
    """Device creation request model."""
    name: str = Field(..., min_length=1, max_length=100, description="Device name")
    device_type: DeviceType = Field(..., description="Device type")
    serial_number: Optional[str] = Field(None, max_length=100, description="Serial number")
    manufacturer: Optional[str] = Field(None, max_length=100, description="Manufacturer")
    model: Optional[str] = Field(None, max_length=100, description="Model")
    firmware_version: Optional[str] = Field(None, max_length=50, description="Firmware version")
    connection_url: Optional[str] = Field(None, max_length=255, description="Connection URL")
    connection_config: Optional[Dict[str, Any]] = Field(None, description="Connection configuration")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class DeviceUpdate(BaseModel):
    """Device update request model."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Device name")
    device_type: Optional[DeviceType] = Field(None, description="Device type")
    serial_number: Optional[str] = Field(None, max_length=100, description="Serial number")
    manufacturer: Optional[str] = Field(None, max_length=100, description="Manufacturer")
    model: Optional[str] = Field(None, max_length=100, description="Model")
    firmware_version: Optional[str] = Field(None, max_length=50, description="Firmware version")
    connection_url: Optional[str] = Field(None, max_length=255, description="Connection URL")
    connection_config: Optional[Dict[str, Any]] = Field(None, description="Connection configuration")
    is_active: Optional[bool] = Field(None, description="Is device active")
    is_online: Optional[bool] = Field(None, description="Is device online")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class DeviceResponse(BaseModel):
    """Device response model."""
    id: int
    name: str
    device_type: str
    serial_number: Optional[str]
    manufacturer: Optional[str]
    model: Optional[str]
    firmware_version: Optional[str]
    connection_url: Optional[str]
    is_active: bool
    is_online: bool
    last_seen: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

