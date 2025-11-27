"""Operation routes."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..auth import get_current_active_user
from ..models.user import User
from ..schemas.operation import OperationCreate, OperationResponse, OperationQuery
from ..schemas.response import ResponseModel
from ..services.operation_service import OperationService

router = APIRouter(prefix="/api/operations", tags=["Operations"])


@router.get("", response_model=ResponseModel[List[OperationResponse]])
async def get_operations(
    query: OperationQuery = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get list of operations with filters."""
    operations = await OperationService.get_operations(db, query)
    return ResponseModel(
        status=status.HTTP_200_OK,
        message="Operations retrieved successfully",
        data=[OperationResponse.model_validate(op) for op in operations]
    )


@router.get("/{operation_id}", response_model=ResponseModel[OperationResponse])
async def get_operation(
    operation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get operation by ID."""
    operation = await OperationService.get_operation(db, operation_id)
    if not operation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Operation not found"
        )
    return ResponseModel(
        status=status.HTTP_200_OK,
        message="Operation retrieved successfully",
        data=OperationResponse.model_validate(operation)
    )

