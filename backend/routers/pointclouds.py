"""Point cloud routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..auth import get_current_active_user
from ..models.user import User
from ..schemas.response import ResponseModel
from ..services.drone_service import DroneService

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None

router = APIRouter(prefix="/api/drones", tags=["Point Clouds"])


@router.get("/{drone_id}/pointcloud", response_model=ResponseModel[dict])
async def get_drone_pointcloud(
    drone_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get latest point cloud data from drone."""
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
        pc_data = client.get_latest_point_cloud()
        if not pc_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No point cloud available"
            )
        
        points, timestamp = pc_data
        
        # Convert numpy array to list for JSON serialization
        # Sample if too large
        if HAS_NUMPY and len(points) > 10000:
            indices = np.random.choice(len(points), 10000, replace=False)
            points = points[indices]
        
        points_list = points.tolist() if HAS_NUMPY else list(points)
        
        return ResponseModel(
            status=status.HTTP_200_OK,
            message="Point cloud retrieved successfully",
            data={
                "points": points_list,
                "timestamp": timestamp,
                "count": len(points_list)
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting point cloud: {str(e)}"
        )


@router.get("/{drone_id}/pointcloud/fetch", response_model=ResponseModel[dict])
async def fetch_drone_pointcloud(
    drone_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Fetch point cloud data synchronously from drone."""
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
        pc_data = client.fetch_point_cloud()
        if not pc_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No point cloud received"
            )
        
        points, timestamp = pc_data
        
        # Sample if too large
        if HAS_NUMPY and len(points) > 10000:
            indices = np.random.choice(len(points), 10000, replace=False)
            points = points[indices]
        
        points_list = points.tolist() if HAS_NUMPY else list(points)
        
        return ResponseModel(
            status=status.HTTP_200_OK,
            message="Point cloud fetched successfully",
            data={
                "points": points_list,
                "timestamp": timestamp,
                "count": len(points_list)
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching point cloud: {str(e)}"
        )

