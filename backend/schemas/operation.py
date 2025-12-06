"""Operation schemas."""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from ..models.operation import OperationType, OperationStatus


class OperationCreate(BaseModel):
    """Operation creation request model."""
    operation_type: OperationType = Field(..., description="Operation type")
    drone_id: Optional[int] = Field(None, description="Drone ID")
    topic: Optional[str] = Field(None, max_length=255, description="Topic name (for publish)")
    service_name: Optional[str] = Field(None, max_length=255, description="Service name (for service calls)")
    payload: Optional[Dict[str, Any]] = Field(None, description="Operation payload")
    extra_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata", alias="metadata")


class OperationQuery(BaseModel):
    """Operation query model."""
    drone_id: Optional[int] = Field(None, description="Filter by drone ID")
    operation_type: Optional[OperationType] = Field(None, description="Filter by operation type")
    status: Optional[OperationStatus] = Field(None, description="Filter by status")
    limit: int = Field(default=100, ge=1, le=1000, description="Limit results")
    offset: int = Field(default=0, ge=0, description="Offset results")


class OperationResponse(BaseModel):
    """Operation response model."""
    id: int
    operation_type: str
    status: str
    user_id: Optional[int]
    drone_id: Optional[int]
    topic: Optional[str]
    service_name: Optional[str]
    payload: Optional[Dict[str, Any]]
    response: Optional[Dict[str, Any]]
    error_message: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    
    class Config:
        from_attributes = True

