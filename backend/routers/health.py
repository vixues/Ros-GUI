"""Health check endpoint for monitoring database and service status."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

from ..database import get_db
from ..schemas.response import ResponseModel
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/health", tags=["Health"])


@router.get("/", response_model=ResponseModel)
async def health_check():
    """Basic health check."""
    return ResponseModel(
        status=status.HTTP_200_OK,
        message="Service is healthy",
        data={
            "status": "healthy",
            "version": settings.APP_VERSION,
            "environment": "debug" if settings.DEBUG else "production"
        }
    )


@router.get("/db", response_model=ResponseModel)
async def database_health_check(db: AsyncSession = Depends(get_db)):
    """Database connectivity check."""
    try:
        await db.execute(text("SELECT 1"))
        return ResponseModel(
            status=status.HTTP_200_OK,
            message="Database connection is healthy",
            data={"database": "connected"}
        )
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return ResponseModel(
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
            message="Database connection failed",
            data={"database": "disconnected", "error": str(e)}
        )


@router.get("/detailed", response_model=ResponseModel)
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """Detailed health check with all service statuses."""
    health_status = {
        "overall": "healthy",
        "services": {}
    }
    
    # Check database
    try:
        await db.execute(text("SELECT 1"))
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        health_status["services"]["database"] = f"unhealthy: {str(e)}"
        health_status["overall"] = "degraded"
    
    # Check cache (if configured)
    if settings.REDIS_URL:
        try:
            from ..cache import redis_client
            if redis_client:
                await redis_client.ping()
                health_status["services"]["cache"] = "healthy"
            else:
                health_status["services"]["cache"] = "not configured"
        except Exception as e:
            health_status["services"]["cache"] = f"unhealthy: {str(e)}"
            health_status["overall"] = "degraded"
    
    response_status = (
        status.HTTP_200_OK if health_status["overall"] == "healthy"
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    
    return ResponseModel(
        status=response_status,
        message=f"System is {health_status['overall']}",
        data=health_status
    )

