"""Log service for business logic."""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from ..models.log import SystemLog, LogLevel
from ..schemas.log import LogFilters


class LogService:
    """Service for log operations."""

    @staticmethod
    async def create_log(
        db: AsyncSession,
        level: LogLevel,
        module: str,
        message: str,
        metadata: Optional[dict] = None,
        user_id: Optional[int] = None
    ) -> SystemLog:
        """Create a new log entry."""
        log = SystemLog(
            level=level,
            module=module,
            message=message,
            extra_metadata=metadata,
            user_id=user_id
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return log

    @staticmethod
    async def get_logs(
        db: AsyncSession,
        filters: LogFilters
    ) -> List[SystemLog]:
        """Get logs with filters."""
        query = select(SystemLog)
        
        if filters.level:
            query = query.where(SystemLog.level == filters.level)
        if filters.module:
            query = query.where(SystemLog.module == filters.module)
        if filters.start_date:
            try:
                start = datetime.fromisoformat(filters.start_date)
                query = query.where(SystemLog.timestamp >= start)
            except ValueError:
                pass
        if filters.end_date:
            try:
                end = datetime.fromisoformat(filters.end_date)
                query = query.where(SystemLog.timestamp <= end)
            except ValueError:
                pass
        
        query = query.offset(filters.offset).limit(filters.limit).order_by(SystemLog.timestamp.desc())
        
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_log(db: AsyncSession, log_id: int) -> Optional[SystemLog]:
        """Get log by ID."""
        result = await db.execute(select(SystemLog).where(SystemLog.id == log_id))
        return result.scalar_one_or_none()

