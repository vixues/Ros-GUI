"""Device management routes."""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..auth import get_current_active_user
from ..models.user import User
from ..schemas.device import DeviceCreate, DeviceUpdate, DeviceResponse
from ..schemas.response import ResponseModel
from ..services.device_service import DeviceService

router = APIRouter(prefix="/api/devices", tags=["Devices"])


@router.post("", response_model=ResponseModel[DeviceResponse], status_code=status.HTTP_201_CREATED)
async def create_device(
    device_data: DeviceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new device."""
    device = await DeviceService.create_device(db, device_data)
    return ResponseModel(
        status=status.HTTP_201_CREATED,
        message="Device created successfully",
        data=DeviceResponse.model_validate(device)
    )


@router.get("", response_model=ResponseModel[List[DeviceResponse]])
async def get_devices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    device_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get list of devices."""
    devices = await DeviceService.get_devices(db, skip=skip, limit=limit, device_type=device_type)
    return ResponseModel(
        status=status.HTTP_200_OK,
        message="Devices retrieved successfully",
        data=[DeviceResponse.model_validate(device) for device in devices]
    )


@router.get("/{device_id}", response_model=ResponseModel[DeviceResponse])
async def get_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get device by ID."""
    device = await DeviceService.get_device(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    return ResponseModel(
        status=status.HTTP_200_OK,
        message="Device retrieved successfully",
        data=DeviceResponse.model_validate(device)
    )


@router.put("/{device_id}", response_model=ResponseModel[DeviceResponse])
async def update_device(
    device_id: int,
    device_data: DeviceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update device."""
    device = await DeviceService.update_device(db, device_id, device_data)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    return ResponseModel(
        status=status.HTTP_200_OK,
        message="Device updated successfully",
        data=DeviceResponse.model_validate(device)
    )


@router.delete("/{device_id}", response_model=ResponseModel[dict])
async def delete_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete device."""
    success = await DeviceService.delete_device(db, device_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    return ResponseModel(
        status=status.HTTP_200_OK,
        message="Device deleted successfully",
        data={"device_id": device_id}
    )

