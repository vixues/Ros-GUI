"""Drone management routes."""
import base64
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..auth import get_current_active_user
from ..models.user import User
from ..schemas.drone import (
    DroneCreate,
    DroneUpdate,
    DroneResponse,
    DroneStatusResponse,
    DroneConnectionRequest,
    DroneStateSnapshot
)
from ..schemas.response import ResponseModel
from ..services.drone_service import DroneService
from ..services.operation_service import OperationService
from ..models.operation import OperationType, OperationStatus

try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    cv2 = None
    np = None

router = APIRouter(prefix="/api/drones", tags=["Drones"])


@router.post("", response_model=ResponseModel[DroneResponse], status_code=status.HTTP_201_CREATED)
async def create_drone(
    drone_data: DroneCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new drone."""
    drone = await DroneService.create_drone(db, drone_data, current_user.id)
    return ResponseModel(
        status=status.HTTP_201_CREATED,
        message="Drone created successfully",
        data=DroneResponse.model_validate(drone)
    )


@router.get("", response_model=ResponseModel[List[DroneResponse]])
async def get_drones(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get list of drones."""
    drones = await DroneService.get_drones(db, skip=skip, limit=limit, status=status)
    return ResponseModel(
        status=status.HTTP_200_OK,
        message="Drones retrieved successfully",
        data=[DroneResponse.model_validate(drone) for drone in drones]
    )


@router.get("/{drone_id}", response_model=ResponseModel[DroneResponse])
async def get_drone(
    drone_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get drone by ID."""
    drone = await DroneService.get_drone(db, drone_id)
    if not drone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drone not found"
        )
    return ResponseModel(
        status=status.HTTP_200_OK,
        message="Drone retrieved successfully",
        data=DroneResponse.model_validate(drone)
    )


@router.put("/{drone_id}", response_model=ResponseModel[DroneResponse])
async def update_drone(
    drone_id: int,
    drone_data: DroneUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update drone."""
    drone = await DroneService.update_drone(db, drone_id, drone_data, current_user.id)
    if not drone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drone not found"
        )
    return ResponseModel(
        status=status.HTTP_200_OK,
        message="Drone updated successfully",
        data=DroneResponse.model_validate(drone)
    )


@router.delete("/{drone_id}", response_model=ResponseModel[dict])
async def delete_drone(
    drone_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete drone."""
    # TODO: Implement delete drone
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Delete drone not implemented"
    )


@router.post("/{drone_id}/connect", response_model=ResponseModel[dict])
async def connect_drone(
    drone_id: int,
    connection_request: DroneConnectionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Connect drone to ROS bridge."""
    success = await DroneService.connect_drone(db, drone_id, connection_request, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to initiate connection"
        )
    return ResponseModel(
        status=status.HTTP_200_OK,
        message="Connection initiated",
        data={"drone_id": drone_id, "status": "connecting"}
    )


@router.post("/{drone_id}/disconnect", response_model=ResponseModel[dict])
async def disconnect_drone(
    drone_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Disconnect drone from ROS bridge."""
    success = await DroneService.disconnect_drone(db, drone_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to disconnect"
        )
    return ResponseModel(
        status=status.HTTP_200_OK,
        message="Disconnected successfully",
        data={"drone_id": drone_id, "status": "disconnected"}
    )


@router.get("/{drone_id}/status", response_model=ResponseModel[DroneStatusResponse])
async def get_drone_status(
    drone_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get drone status."""
    drone = await DroneService.get_drone(db, drone_id)
    if not drone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drone not found"
        )
    
    # Get ROS client and update state if connected
    client = DroneService.get_drone_client(drone_id)
    if client and client.is_connected():
        try:
            state = client.get_status()
            pos = client.get_position()
            ori = client.get_orientation()
            
            # Update drone state in database
            await DroneService.update_drone_state(db, drone_id, {
                "is_connected": state.connected,
                "is_armed": state.armed,
                "mode": state.mode,
                "battery": state.battery,
                "latitude": pos[0],
                "longitude": pos[1],
                "altitude": pos[2],
                "roll": ori[0],
                "pitch": ori[1],
                "yaw": ori[2],
                "landed": state.landed,
                "reached": state.reached,
                "returned": state.returned,
                "tookoff": state.tookoff
            })
            
            await db.refresh(drone)
        except Exception as e:
            pass  # Ignore errors, use cached state
    
    state_snapshot = DroneStateSnapshot(
        is_connected=drone.is_connected,
        is_armed=drone.is_armed,
        mode=drone.mode,
        battery=drone.battery,
        latitude=drone.latitude,
        longitude=drone.longitude,
        altitude=drone.altitude,
        roll=drone.roll,
        pitch=drone.pitch,
        yaw=drone.yaw,
        landed=drone.landed,
        reached=drone.reached,
        returned=drone.returned,
        tookoff=drone.tookoff,
        last_state_update=drone.last_state_update
    )
    
    status_response = DroneStatusResponse(
        drone_id=drone.id,
        name=drone.name,
        status=drone.status,
        is_connected=drone.is_connected,
        state=state_snapshot
    )
    
    return ResponseModel(
        status=status.HTTP_200_OK,
        message="Status retrieved successfully",
        data=status_response
    )


@router.post("/{drone_id}/publish", response_model=ResponseModel[dict])
async def publish_to_drone(
    drone_id: int,
    topic: str,
    topic_type: str,
    message: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Publish message to ROS topic."""
    drone = await DroneService.get_drone(db, drone_id)
    if not drone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drone not found"
        )
    
    client = DroneService.get_drone_client(drone_id)
    if not client or not client.is_connected():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Drone not connected"
        )
    
    # Create operation record
    from ..schemas.operation import OperationCreate
    operation_data = OperationCreate(
        operation_type=OperationType.PUBLISH,
        drone_id=drone_id,
        topic=topic,
        payload=message
    )
    operation = await OperationService.create_operation(db, operation_data, current_user.id)
    
    try:
        client.publish(topic, topic_type, message)
        await OperationService.update_operation_status(
            db, operation.id, OperationStatus.SUCCESS, response={"published": True}
        )
        return ResponseModel(
            status=status.HTTP_200_OK,
            message="Message published successfully",
            data={"topic": topic, "operation_id": operation.id}
        )
    except Exception as e:
        await OperationService.update_operation_status(
            db, operation.id, OperationStatus.FAILED, error_message=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish: {str(e)}"
        )

