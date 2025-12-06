"""Recording schemas."""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from ..models.recording import RecordingStatus


class RecordingCreate(BaseModel):
    """Recording creation request model."""
    drone_id: int = Field(..., description="Drone ID")
    name: str = Field(..., min_length=1, max_length=255, description="Recording name")
    record_images: bool = Field(default=True, description="Record images")
    record_pointclouds: bool = Field(default=True, description="Record point clouds")
    record_states: bool = Field(default=True, description="Record states")
    image_quality: int = Field(default=85, ge=0, le=100, description="Image quality (0-100)")
    extra_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata", alias="metadata")


class RecordingUpdate(BaseModel):
    """Recording update request model."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Recording name")
    status: Optional[RecordingStatus] = Field(None, description="Recording status")
    extra_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata", alias="metadata")


class RecordingResponse(BaseModel):
    """Recording response model."""
    id: int
    drone_id: int
    name: str
    status: str
    record_images: bool
    record_pointclouds: bool
    record_states: bool
    image_quality: int
    file_path: Optional[str]
    file_size_bytes: Optional[int]
    duration_seconds: Optional[float]
    image_count: int
    pointcloud_count: int
    state_count: int
    started_at: Optional[datetime]
    stopped_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

