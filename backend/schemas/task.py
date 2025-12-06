"""Task schemas."""
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

from ..models.task import TaskStatus, TaskPriority


class TaskCreate(BaseModel):
    """Task creation request model."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None)
    status: Optional[TaskStatus] = Field(TaskStatus.PENDING)
    priority: Optional[TaskPriority] = Field(TaskPriority.MEDIUM)
    assigned_drone_ids: Optional[List[int]] = Field(default_factory=list)


class TaskUpdate(BaseModel):
    """Task update request model."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None)
    status: Optional[TaskStatus] = Field(None)
    priority: Optional[TaskPriority] = Field(None)
    assigned_drone_ids: Optional[List[int]] = Field(None)


class TaskResponse(BaseModel):
    """Task response model."""
    id: int
    title: str
    description: Optional[str]
    status: str
    priority: str
    assigned_drone_ids: List[int]
    created_by: int
    updated_by: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

