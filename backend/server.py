#!/usr/bin/env python
"""Backend server for ROS GUI using FastAPI - Professional Multi-Drone Management Platform."""
import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager

# Add project root to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import settings
from .database import init_db, close_db
from .cache import close_redis
from .middleware import LoggingMiddleware, ExceptionHandlerMiddleware
from .schemas.response import ErrorResponse
from .routers import (
    auth_router,
    devices_router,
    drones_router,
    operations_router,
    recordings_router,
    agent_router,
    images_router,
    pointclouds_router
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown.
    
    Handles:
    - Database initialization
    - Redis connection
    - Cleanup on shutdown
    """
    logger.info("Starting backend server...")
    logger.info(f"Environment: {'DEBUG' if settings.DEBUG else 'PRODUCTION'}")
    
    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    yield
    
    logger.info("Shutting down backend server...")
    
    # Close database connections
    try:
        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")
    
    # Close Redis connections
    try:
        await close_redis()
        logger.info("Redis connections closed")
    except Exception as e:
        logger.error(f"Error closing Redis: {e}")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Professional Multi-Drone Management and Control Platform with LLM Agent Support",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(ExceptionHandlerMiddleware)


# Global exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            status=exc.status_code,
            message=exc.detail,
            error_code=f"HTTP_{exc.status_code}"
        ).dict()
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="Validation error",
            detail=str(exc),
            error_code="VALIDATION_ERROR"
        ).dict()
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Internal server error",
            detail=str(exc) if settings.DEBUG else "An error occurred",
            error_code="INTERNAL_ERROR"
        ).dict()
    )


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION
    }


# Include routers
app.include_router(auth_router)
app.include_router(devices_router)
app.include_router(drones_router)
app.include_router(operations_router)
app.include_router(recordings_router)
app.include_router(agent_router)
app.include_router(images_router)
app.include_router(pointclouds_router)


def main():
    """Main entry point."""
    import uvicorn
    uvicorn.run(
        "backend.server:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower(),
        reload=settings.DEBUG
    )


if __name__ == "__main__":
    main()
