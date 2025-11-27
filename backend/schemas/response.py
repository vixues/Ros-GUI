"""Unified response models."""
from typing import Optional, Any, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseModel(BaseModel, Generic[T]):
    """
    Unified API response model.
    
    All API responses must use this format with:
    - status: HTTP status code
    - message: Human-readable message
    - data: Response data (optional)
    """
    status: int = Field(..., description="HTTP status code")
    message: str = Field(..., description="Human-readable message")
    data: Optional[T] = Field(None, description="Response data")


class ErrorResponse(BaseModel):
    """
    Error response model.
    
    Used for error responses with detailed error information.
    """
    status: int = Field(..., description="HTTP status code")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    error_code: Optional[str] = Field(None, description="Error code")

