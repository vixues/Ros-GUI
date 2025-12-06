"""Operation service for managing operations."""
import logging
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from ..models.operation import Operation, OperationType, OperationStatus
from ..schemas.operation import OperationCreate, OperationQuery

logger = logging.getLogger(__name__)


class OperationService:
    """Service for managing operations."""
    
    @staticmethod
    async def create_operation(
        db: AsyncSession,
        operation_data: OperationCreate,
        user_id: Optional[int] = None
    ) -> Operation:
        """
        Create a new operation.
        
        Args:
            db: Database session
            operation_data: Operation creation data
            user_id: User ID
            
        Returns:
            Created operation
        """
        operation = Operation(
            operation_type=operation_data.operation_type,
            status=OperationStatus.PENDING,
            user_id=user_id,
            drone_id=operation_data.drone_id,
            topic=operation_data.topic,
            service_name=operation_data.service_name,
            payload=operation_data.payload,
            extra_metadata=operation_data.extra_metadata if hasattr(operation_data, 'extra_metadata') else getattr(operation_data, 'metadata', None)
        )
        db.add(operation)
        await db.commit()
        await db.refresh(operation)
        
        logger.info(f"Created operation: {operation.id} ({operation.operation_type.value})")
        return operation
    
    @staticmethod
    async def get_operation(db: AsyncSession, operation_id: int) -> Optional[Operation]:
        """
        Get operation by ID.
        
        Args:
            db: Database session
            operation_id: Operation ID
            
        Returns:
            Operation or None
        """
        result = await db.execute(select(Operation).where(Operation.id == operation_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_operations(
        db: AsyncSession,
        query: OperationQuery
    ) -> List[Operation]:
        """
        Get list of operations with filters.
        
        Args:
            db: Database session
            query: Query parameters
            
        Returns:
            List of operations
        """
        conditions = []
        
        if query.drone_id:
            conditions.append(Operation.drone_id == query.drone_id)
        if query.operation_type:
            conditions.append(Operation.operation_type == query.operation_type)
        if query.status:
            conditions.append(Operation.status == query.status)
        
        query_stmt = select(Operation)
        if conditions:
            query_stmt = query_stmt.where(and_(*conditions))
        
        query_stmt = query_stmt.order_by(Operation.started_at.desc())
        query_stmt = query_stmt.offset(query.offset).limit(query.limit)
        
        result = await db.execute(query_stmt)
        return list(result.scalars().all())
    
    @staticmethod
    async def update_operation_status(
        db: AsyncSession,
        operation_id: int,
        status: OperationStatus,
        response: Optional[dict] = None,
        error_message: Optional[str] = None
    ) -> Optional[Operation]:
        """
        Update operation status.
        
        Args:
            db: Database session
            operation_id: Operation ID
            status: New status
            response: Operation response
            error_message: Error message if failed
            
        Returns:
            Updated operation or None
        """
        operation = await OperationService.get_operation(db, operation_id)
        if not operation:
            return None
        
        operation.status = status
        if response:
            operation.response = response
        if error_message:
            operation.error_message = error_message
        
        if status in [OperationStatus.SUCCESS, OperationStatus.FAILED, OperationStatus.CANCELLED]:
            operation.completed_at = datetime.utcnow()
            if operation.started_at:
                duration = (operation.completed_at - operation.started_at).total_seconds()
                operation.duration_seconds = duration
        
        await db.commit()
        await db.refresh(operation)
        
        logger.info(f"Updated operation {operation_id} status to {status.value}")
        return operation

