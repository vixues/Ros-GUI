"""Enhanced middleware with request ID tracking and performance monitoring."""
import time
import uuid
import logging
import traceback
from typing import Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from contextvars import ContextVar

from .schemas.response import ErrorResponse
from .config import settings

logger = logging.getLogger(__name__)

# Context variable for request ID
request_id_ctx_var: ContextVar[str] = ContextVar('request_id', default='')


def get_request_id() -> str:
    """Get current request ID from context."""
    return request_id_ctx_var.get()


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Middleware for adding request ID to all requests."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add request ID."""
        request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())
        request_id_ctx_var.set(request_id)
        
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers['X-Request-ID'] = request_id
        
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Enhanced middleware for logging API requests and responses with performance metrics."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response with detailed metrics."""
        start_time = time.time()
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        # Log request
        logger.info(
            f"[{request_id}] Request: {request.method} {request.url.path} - "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )
        
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Determine log level based on status and duration
            log_level = logging.INFO
            if response.status_code >= 500:
                log_level = logging.ERROR
            elif response.status_code >= 400:
                log_level = logging.WARNING
            elif duration > 1.0:  # Slow request warning
                log_level = logging.WARNING
            
            # Log response
            logger.log(
                log_level,
                f"[{request_id}] Response: {request.method} {request.url.path} - "
                f"Status: {response.status_code} - "
                f"Duration: {duration:.3f}s"
            )
            
            # Add performance headers
            response.headers["X-Process-Time"] = f"{duration:.3f}"
            response.headers["X-Request-ID"] = request_id
            
            # Alert on slow requests
            if duration > 2.0:
                logger.warning(
                    f"[{request_id}] SLOW REQUEST: {request.method} {request.url.path} "
                    f"took {duration:.3f}s"
                )
            
            return response
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"[{request_id}] Error: {request.method} {request.url.path} - "
                f"Exception: {str(e)} - "
                f"Duration: {duration:.3f}s"
            )
            logger.error(f"[{request_id}] {traceback.format_exc()}")
            raise


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """Enhanced middleware for handling exceptions globally with proper error tracking."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle exceptions with request context."""
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        try:
            return await call_next(request)
        except Exception as e:
            logger.error(f"[{request_id}] Unhandled exception: {str(e)}")
            logger.error(f"[{request_id}] {traceback.format_exc()}")
            
            # Determine status code based on exception type
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            error_code = "INTERNAL_ERROR"
            message = "Internal server error"
            
            # Customize based on exception type
            if hasattr(e, 'status_code'):
                status_code = e.status_code
            
            error_response = ErrorResponse(
                status=status_code,
                message=message,
                detail=str(e) if settings.DEBUG else "An error occurred",
                error_code=error_code
            )
            
            return JSONResponse(
                status_code=status_code,
                content=error_response.dict(),
                headers={'X-Request-ID': request_id}
            )


class CORSSecurityMiddleware(BaseHTTPMiddleware):
    """Enhanced CORS middleware with security headers."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers."""
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response
