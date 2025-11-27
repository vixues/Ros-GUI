"""FastAPI middleware for logging and exception handling."""
import time
import logging
import traceback
from typing import Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .schemas.response import ErrorResponse
from .config import settings

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging API requests and responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response."""
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} - "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )
        
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            logger.info(
                f"Response: {request.method} {request.url.path} - "
                f"Status: {response.status_code} - "
                f"Duration: {duration:.3f}s"
            )
            
            # Add duration header
            response.headers["X-Process-Time"] = str(duration)
            
            return response
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Error: {request.method} {request.url.path} - "
                f"Exception: {str(e)} - "
                f"Duration: {duration:.3f}s"
            )
            logger.error(traceback.format_exc())
            raise


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for handling exceptions globally."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle exceptions."""
        try:
            return await call_next(request)
        except Exception as e:
            logger.error(f"Unhandled exception: {str(e)}")
            logger.error(traceback.format_exc())
            
            error_response = ErrorResponse(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Internal server error",
                detail=str(e) if settings.DEBUG else "An error occurred",
                error_code="INTERNAL_ERROR"
            )
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=error_response.dict()
            )

