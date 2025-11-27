"""Recording routes."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..auth import get_current_active_user
from ..models.user import User
from ..schemas.recording import RecordingCreate, RecordingUpdate, RecordingResponse
from ..schemas.response import ResponseModel
from ..services.recording_service import RecordingService
from ..services.drone_service import DroneService

router = APIRouter(prefix="/api/recordings", tags=["Recordings"])


@router.post("", response_model=ResponseModel[RecordingResponse], status_code=status.HTTP_201_CREATED)
async def create_recording(
    recording_data: RecordingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new recording."""
    recording = await RecordingService.create_recording(db, recording_data)
    return ResponseModel(
        status=status.HTTP_201_CREATED,
        message="Recording created successfully",
        data=RecordingResponse.model_validate(recording)
    )


@router.get("", response_model=ResponseModel[List[RecordingResponse]])
async def get_recordings(
    drone_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get list of recordings."""
    recordings = await RecordingService.get_recordings(db, drone_id=drone_id, skip=skip, limit=limit)
    return ResponseModel(
        status=status.HTTP_200_OK,
        message="Recordings retrieved successfully",
        data=[RecordingResponse.model_validate(rec) for rec in recordings]
    )


@router.get("/{recording_id}", response_model=ResponseModel[RecordingResponse])
async def get_recording(
    recording_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get recording by ID."""
    recording = await RecordingService.get_recording(db, recording_id)
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found"
        )
    return ResponseModel(
        status=status.HTTP_200_OK,
        message="Recording retrieved successfully",
        data=RecordingResponse.model_validate(recording)
    )


@router.post("/{recording_id}/start", response_model=ResponseModel[RecordingResponse])
async def start_recording(
    recording_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Start recording."""
    recording = await RecordingService.start_recording(db, recording_id)
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found"
        )
    
    # Start recording on drone client
    drone = await DroneService.get_drone(db, recording.drone_id)
    if drone:
        client = DroneService.get_drone_client(recording.drone_id)
        if client and client.is_connected():
            try:
                client.start_recording(
                    record_images=recording.record_images,
                    record_pointclouds=recording.record_pointclouds,
                    record_states=recording.record_states,
                    image_quality=recording.image_quality
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to start recording on drone: {str(e)}"
                )
    
    return ResponseModel(
        status=status.HTTP_200_OK,
        message="Recording started successfully",
        data=RecordingResponse.model_validate(recording)
    )


@router.post("/{recording_id}/stop", response_model=ResponseModel[RecordingResponse])
async def stop_recording(
    recording_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Stop recording."""
    recording = await RecordingService.get_recording(db, recording_id)
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found"
        )
    
    # Stop recording on drone client
    drone = await DroneService.get_drone(db, recording.drone_id)
    if drone:
        client = DroneService.get_drone_client(recording.drone_id)
        if client and client.is_connected():
            try:
                client.stop_recording()
            except Exception as e:
                pass  # Ignore errors, just stop in database
    
    recording = await RecordingService.stop_recording(db, recording_id)
    
    return ResponseModel(
        status=status.HTTP_200_OK,
        message="Recording stopped successfully",
        data=RecordingResponse.model_validate(recording)
    )

