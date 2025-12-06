"""Enhanced task service with proper error handling and validation."""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
import logging

from ..models.task import Task, TaskStatus, TaskPriority
from ..schemas.task import TaskCreate, TaskUpdate

logger = logging.getLogger(__name__)


class TaskService:
    """Service for task operations with enhanced error handling."""

    @staticmethod
    async def create_task(
        db: AsyncSession,
        task_data: TaskCreate,
        user_id: int
    ) -> Task:
        """
        Create a new task.
        
        Args:
            db: Database session
            task_data: Task creation data
            user_id: User ID
            
        Returns:
            Created task
            
        Raises:
            IntegrityError: If task validation fails
        """
        try:
            task = Task(
                title=task_data.title,
                description=task_data.description,
                status=task_data.status or TaskStatus.PENDING,
                priority=task_data.priority or TaskPriority.MEDIUM,
                assigned_drone_ids=task_data.assigned_drone_ids or [],
                created_by=user_id,
                updated_by=user_id
            )
            db.add(task)
            await db.flush()
            await db.refresh(task)
            
            logger.info(f"Created task: {task.id} by user {user_id}")
            return task
            
        except IntegrityError as e:
            logger.error(f"Task creation failed: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def get_tasks(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[Task]:
        """
        Get list of tasks with filters.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Filter by status
            priority: Filter by priority
            
        Returns:
            List of tasks
        """
        try:
            query = select(Task)
            
            if status:
                query = query.where(Task.status == status)
            if priority:
                query = query.where(Task.priority == priority)
            
            query = query.offset(skip).limit(limit).order_by(Task.created_at.desc())
            
            result = await db.execute(query)
            tasks = result.scalars().all()
            
            logger.debug(f"Retrieved {len(tasks)} tasks")
            return tasks
            
        except Exception as e:
            logger.error(f"Failed to retrieve tasks: {e}")
            return []

    @staticmethod
    async def get_task(db: AsyncSession, task_id: int) -> Optional[Task]:
        """
        Get task by ID.
        
        Args:
            db: Database session
            task_id: Task ID
            
        Returns:
            Task or None
        """
        try:
            result = await db.execute(select(Task).where(Task.id == task_id))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to retrieve task {task_id}: {e}")
            return None

    @staticmethod
    async def update_task(
        db: AsyncSession,
        task_id: int,
        task_data: TaskUpdate,
        user_id: int
    ) -> Optional[Task]:
        """
        Update task.
        
        Args:
            db: Database session
            task_id: Task ID
            task_data: Task update data
            user_id: User ID
            
        Returns:
            Updated task or None
        """
        try:
            task = await TaskService.get_task(db, task_id)
            if not task:
                logger.warning(f"Task {task_id} not found for update")
                return None
            
            # Update only provided fields
            update_data = task_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(task, field, value)
            
            task.updated_by = user_id
            
            await db.flush()
            await db.refresh(task)
            
            logger.info(f"Updated task: {task_id} by user {user_id}")
            return task
            
        except Exception as e:
            logger.error(f"Failed to update task {task_id}: {e}")
            await db.rollback()
            return None

    @staticmethod
    async def delete_task(db: AsyncSession, task_id: int) -> bool:
        """
        Delete task.
        
        Args:
            db: Database session
            task_id: Task ID
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            task = await TaskService.get_task(db, task_id)
            if not task:
                logger.warning(f"Task {task_id} not found for deletion")
                return False
            
            await db.delete(task)
            await db.flush()
            
            logger.info(f"Deleted task: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete task {task_id}: {e}")
            await db.rollback()
            return False
