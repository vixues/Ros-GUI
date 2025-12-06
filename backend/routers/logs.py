"""System logs routes."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..auth import get_current_active_user
from ..models.user import User
from ..schemas.log import LogResponse, LogFilters
from ..schemas.response import ResponseModel
from ..services.log_service import LogService

router = APIRouter(prefix="/api/logs", tags=["Logs"])


@router.get("", response_model=ResponseModel[List[LogResponse]])
async def get_logs(
    level: Optional[str] = Query(None),
    module: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get system logs with filters."""
    filters = LogFilters(
        level=level,
        module=module,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )
    logs = await LogService.get_logs(db, filters)
    return ResponseModel(
        status=status.HTTP_200_OK,
        message="Logs retrieved successfully",
        data=[LogResponse.model_validate(log) for log in logs]
    )


@router.get("/{log_id}", response_model=ResponseModel[LogResponse])
async def get_log(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get log by ID."""
    log = await LogService.get_log(db, log_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log not found"
        )
    return ResponseModel(
        status=status.HTTP_200_OK,
        message="Log retrieved successfully",
        data=LogResponse.model_validate(log)
    )

