"""Task management routes."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..auth import get_current_active_user
from ..models.user import User
from ..schemas.task import TaskCreate, TaskUpdate, TaskResponse
from ..schemas.response import ResponseModel
from ..services.task_service import TaskService

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


@router.post("", response_model=ResponseModel[TaskResponse], status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new task."""
    task = await TaskService.create_task(db, task_data, current_user.id)
    return ResponseModel(
        status=status.HTTP_201_CREATED,
        message="Task created successfully",
        data=TaskResponse.model_validate(task)
    )


@router.get("", response_model=ResponseModel[List[TaskResponse]])
async def get_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get list of tasks."""
    tasks = await TaskService.get_tasks(
        db, 
        skip=skip, 
        limit=limit, 
        status=status,
        priority=priority
    )
    return ResponseModel(
        status=status.HTTP_200_OK,
        message="Tasks retrieved successfully",
        data=[TaskResponse.model_validate(task) for task in tasks]
    )


@router.get("/{task_id}", response_model=ResponseModel[TaskResponse])
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get task by ID."""
    task = await TaskService.get_task(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return ResponseModel(
        status=status.HTTP_200_OK,
        message="Task retrieved successfully",
        data=TaskResponse.model_validate(task)
    )


@router.put("/{task_id}", response_model=ResponseModel[TaskResponse])
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update task."""
    task = await TaskService.update_task(db, task_id, task_data, current_user.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return ResponseModel(
        status=status.HTTP_200_OK,
        message="Task updated successfully",
        data=TaskResponse.model_validate(task)
    )


@router.delete("/{task_id}", response_model=ResponseModel[dict])
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete task."""
    success = await TaskService.delete_task(db, task_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return ResponseModel(
        status=status.HTTP_200_OK,
        message="Task deleted successfully",
        data={"deleted": True}
    )

