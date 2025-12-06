"""Log schemas."""
from typing import Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime

from ..models.log import LogLevel


class LogFilters(BaseModel):
    """Log filters model."""
    level: Optional[str] = None
    module: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)


class LogResponse(BaseModel):
    """Log response model."""
    id: int
    timestamp: datetime
    level: str
    module: str
    message: str
    extra_metadata: Optional[Any] = Field(None, alias="metadata")
    user_id: Optional[int]

    class Config:
        from_attributes = True

