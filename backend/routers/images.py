"""Image routes."""
import base64
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..auth import get_current_active_user
from ..models.user import User
from ..schemas.response import ResponseModel
from ..services.drone_service import DroneService

try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    cv2 = None
    np = None

router = APIRouter(prefix="/api/drones", tags=["Images"])


@router.get("/{drone_id}/image", response_model=ResponseModel[dict])
async def get_drone_image(
    drone_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get latest camera image from drone."""
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
    
    try:
        image_data = client.get_latest_image()
        if not image_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No image available"
            )
        
        frame, timestamp = image_data
        
        if not HAS_CV2:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OpenCV not available"
            )
        
        # Encode image as JPEG
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return ResponseModel(
            status=status.HTTP_200_OK,
            message="Image retrieved successfully",
            data={
                "image": image_base64,
                "timestamp": timestamp,
                "width": frame.shape[1],
                "height": frame.shape[0],
                "format": "jpeg"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting image: {str(e)}"
        )


@router.get("/{drone_id}/image/fetch", response_model=ResponseModel[dict])
async def fetch_drone_image(
    drone_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Fetch camera image synchronously from drone."""
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
    
    try:
        image_data = client.fetch_camera_image()
        if not image_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No image received"
            )
        
        frame, timestamp = image_data
        
        if not HAS_CV2:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OpenCV not available"
            )
        
        # Encode image as JPEG
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return ResponseModel(
            status=status.HTTP_200_OK,
            message="Image fetched successfully",
            data={
                "image": image_base64,
                "timestamp": timestamp,
                "width": frame.shape[1],
                "height": frame.shape[0],
                "format": "jpeg"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching image: {str(e)}"
        )

