"""Drone service for managing drones and ROS connections."""
import asyncio
import logging
import threading
import time
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from ..models.drone import Drone, DroneStatus, DroneConnection
from ..models.operation import Operation, OperationType, OperationStatus
from ..schemas.drone import DroneCreate, DroneUpdate, DroneConnectionRequest
from ..cache import get_cache, set_cache, delete_cache
from ..models.operation import Operation

try:
    from rosclient import RosClient, MockRosClient
except ImportError:
    RosClient = None
    MockRosClient = None

logger = logging.getLogger(__name__)

# Global drone client registry
_drone_clients: Dict[int, Any] = {}
_clients_lock = threading.Lock()


class DroneService:
    """Service for managing drones."""
    
    @staticmethod
    async def create_drone(db: AsyncSession, drone_data: DroneCreate, user_id: Optional[int] = None) -> Drone:
        """
        Create a new drone.
        
        Args:
            db: Database session
            drone_data: Drone creation data
            user_id: User ID (for operation logging)
            
        Returns:
            Created drone
        """
        drone = Drone(
            name=drone_data.name,
            drone_id=drone_data.drone_id,
            device_id=drone_data.device_id,
            connection_url=drone_data.connection_url,
            use_mock=drone_data.use_mock,
            mock_config=drone_data.mock_config,
            extra_metadata=drone_data.extra_metadata if hasattr(drone_data, 'extra_metadata') else getattr(drone_data, 'metadata', None),
            status=DroneStatus.IDLE.value
        )
        db.add(drone)
        await db.flush()
        
        # Log operation
        if user_id:
            operation = Operation(
                operation_type=OperationType.OTHER,
                status=OperationStatus.SUCCESS,
                user_id=user_id,
                drone_id=drone.id,
                payload={"action": "create_drone", "drone_data": drone_data.dict()},
                extra_metadata={"drone_id": drone.drone_id}
            )
            db.add(operation)
        
        await db.commit()
        await db.refresh(drone)
        
        # Clear cache
        await delete_cache(f"drone:{drone.id}")
        await delete_cache("drones:list")
        
        logger.info(f"Created drone: {drone.id} ({drone.drone_id})")
        return drone
    
    @staticmethod
    async def get_drone(db: AsyncSession, drone_id: int) -> Optional[Drone]:
        """
        Get drone by ID.
        
        Args:
            db: Database session
            drone_id: Drone ID
            
        Returns:
            Drone or None
        """
        # Try cache first
        cache_key = f"drone:{drone_id}"
        cached = await get_cache(cache_key)
        if cached:
            return cached
        
        result = await db.execute(
            select(Drone)
            .where(Drone.id == drone_id)
            .options(selectinload(Drone.device))
        )
        drone = result.scalar_one_or_none()
        
        if drone:
            await set_cache(cache_key, drone, expire=60)
        
        return drone
    
    @staticmethod
    async def get_drones(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[Drone]:
        """
        Get list of drones.
        
        Args:
            db: Database session
            skip: Skip records
            limit: Limit records
            status: Filter by status
            
        Returns:
            List of drones
        """
        query = select(Drone).options(selectinload(Drone.device))
        
        if status:
            query = query.where(Drone.status == status)
        
        query = query.offset(skip).limit(limit).order_by(Drone.created_at.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def update_drone(
        db: AsyncSession,
        drone_id: int,
        drone_data: DroneUpdate,
        user_id: Optional[int] = None
    ) -> Optional[Drone]:
        """
        Update drone.
        
        Args:
            db: Database session
            drone_id: Drone ID
            drone_data: Update data
            user_id: User ID (for operation logging)
            
        Returns:
            Updated drone or None
        """
        drone = await DroneService.get_drone(db, drone_id)
        if not drone:
            return None
        
        update_data = drone_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(drone, key, value)
        
        drone.updated_at = datetime.utcnow()
        
        # Log operation
        if user_id:
            operation = Operation(
                operation_type=OperationType.OTHER,
                status=OperationStatus.SUCCESS,
                user_id=user_id,
                drone_id=drone.id,
                payload={"action": "update_drone", "update_data": update_data},
                extra_metadata={"drone_id": drone.drone_id}
            )
            db.add(operation)
        
        await db.commit()
        await db.refresh(drone)
        
        # Clear cache
        await delete_cache(f"drone:{drone_id}")
        await delete_cache("drones:list")
        
        logger.info(f"Updated drone: {drone_id}")
        return drone
    
    @staticmethod
    async def connect_drone(
        db: AsyncSession,
        drone_id: int,
        connection_request: DroneConnectionRequest,
        user_id: Optional[int] = None
    ) -> bool:
        """
        Connect drone to ROS bridge.
        
        Args:
            db: Database session
            drone_id: Drone ID
            connection_request: Connection request
            user_id: User ID (for operation logging)
            
        Returns:
            True if connection initiated successfully
        """
        drone = await DroneService.get_drone(db, drone_id)
        if not drone:
            return False
        
        if not RosClient:
            logger.error("RosClient not available")
            return False
        
        # Disconnect existing connection
        await DroneService.disconnect_drone(db, drone_id, user_id)
        
        # Update drone connection info
        drone.connection_url = connection_request.connection_url
        drone.use_mock = connection_request.use_mock
        drone.mock_config = connection_request.mock_config
        drone.status = DroneStatus.CONNECTING.value
        
        # Create connection record
        connection = DroneConnection(
            drone_id=drone.id,
            connection_url=connection_request.connection_url,
            connected_at=datetime.utcnow()
        )
        db.add(connection)
        await db.flush()
        
        # Log operation
        if user_id:
            operation = Operation(
                operation_type=OperationType.CONNECT,
                status=OperationStatus.IN_PROGRESS,
                user_id=user_id,
                drone_id=drone.id,
                payload={"connection_url": connection_request.connection_url, "use_mock": connection_request.use_mock},
                metadata={"connection_id": connection.id}
            )
            db.add(operation)
            await db.flush()
            operation_id = operation.id
        else:
            operation_id = None
        
        await db.commit()
        
        # Connect in background thread
        def connect_thread():
            try:
                if connection_request.use_mock:
                    config = connection_request.mock_config or {}
                    client = MockRosClient(connection_request.connection_url, config=config)
                    client.connect_async()
                else:
                    client = RosClient(connection_request.connection_url)
                    client.connect_async()
                
                # Wait for connection
                time.sleep(2)
                
                if client.is_connected():
                    with _clients_lock:
                        _drone_clients[drone_id] = client
                    
                    # Update drone status
                    asyncio.create_task(DroneService._update_drone_connection_status(
                        db, drone_id, connection.id, True, operation_id
                    ))
                    logger.info(f"Connected drone {drone_id} to {connection_request.connection_url}")
                else:
                    logger.warning(f"Connection failed for drone {drone_id}")
                    asyncio.create_task(DroneService._update_drone_connection_status(
                        db, drone_id, connection.id, False, operation_id, "Connection timeout"
                    ))
            except Exception as e:
                logger.error(f"Connection error for drone {drone_id}: {e}")
                asyncio.create_task(DroneService._update_drone_connection_status(
                    db, drone_id, connection.id, False, operation_id, str(e)
                ))
        
        threading.Thread(target=connect_thread, daemon=True).start()
        
        return True
    
    @staticmethod
    async def _update_drone_connection_status(
        db: AsyncSession,
        drone_id: int,
        connection_id: int,
        success: bool,
        operation_id: Optional[int] = None,
        error_message: Optional[str] = None
    ):
        """Update drone connection status (internal async method)."""
        # Create new session for async operation
        from ..database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            try:
                drone = await DroneService.get_drone(session, drone_id)
                if not drone:
                    return
                
                if success:
                    drone.status = DroneStatus.CONNECTED.value
                    drone.is_connected = True
                else:
                    drone.status = DroneStatus.DISCONNECTED.value
                    drone.is_connected = False
                
                # Update connection record
                await session.execute(
                    update(DroneConnection)
                    .where(DroneConnection.id == connection_id)
                    .values(
                        disconnected_at=datetime.utcnow() if not success else None,
                        disconnect_reason=error_message if not success else None
                    )
                )
                
                # Update operation
                if operation_id:
                    op_status = OperationStatus.SUCCESS if success else OperationStatus.FAILED
                    await session.execute(
                        update(Operation)
                        .where(Operation.id == operation_id)
                        .values(
                            status=op_status,
                            completed_at=datetime.utcnow(),
                            error_message=error_message if not success else None
                        )
                    )
                
                await session.commit()
                
                # Clear cache
                await delete_cache(f"drone:{drone_id}")
            except Exception as e:
                logger.error(f"Error updating connection status: {e}")
                await session.rollback()
    
    @staticmethod
    async def disconnect_drone(
        db: AsyncSession,
        drone_id: int,
        user_id: Optional[int] = None
    ) -> bool:
        """
        Disconnect drone from ROS bridge.
        
        Args:
            db: Database session
            drone_id: Drone ID
            user_id: User ID (for operation logging)
            
        Returns:
            True if disconnection successful
        """
        drone = await DroneService.get_drone(db, drone_id)
        if not drone:
            return False
        
        # Disconnect client
        with _clients_lock:
            client = _drone_clients.pop(drone_id, None)
            if client:
                try:
                    client.terminate()
                except Exception as e:
                    logger.error(f"Error terminating client: {e}")
        
        # Update drone status
        drone.status = DroneStatus.DISCONNECTED.value
        drone.is_connected = False
        
        # Update connection record
        await db.execute(
            update(DroneConnection)
            .where(DroneConnection.drone_id == drone_id)
            .where(DroneConnection.disconnected_at.is_(None))
            .values(
                disconnected_at=datetime.utcnow(),
                disconnect_reason="Manual disconnect"
            )
        )
        
        # Log operation
        if user_id:
            operation = Operation(
                operation_type=OperationType.DISCONNECT,
                status=OperationStatus.SUCCESS,
                user_id=user_id,
                drone_id=drone.id,
                payload={"action": "disconnect"},
                extra_metadata={"drone_id": drone.drone_id}
            )
            db.add(operation)
        
        await db.commit()
        
        # Clear cache
        await delete_cache(f"drone:{drone_id}")
        
        logger.info(f"Disconnected drone: {drone_id}")
        return True
    
    @staticmethod
    def get_drone_client(drone_id: int) -> Optional[Any]:
        """
        Get ROS client for drone.
        
        Args:
            drone_id: Drone ID
            
        Returns:
            ROS client or None
        """
        with _clients_lock:
            return _drone_clients.get(drone_id)
    
    @staticmethod
    async def update_drone_state(
        db: AsyncSession,
        drone_id: int,
        state_data: Dict[str, Any]
    ) -> bool:
        """
        Update drone state from ROS.
        
        Args:
            db: Database session
            drone_id: Drone ID
            state_data: State data
            
        Returns:
            True if update successful
        """
        drone = await DroneService.get_drone(db, drone_id)
        if not drone:
            return False
        
        # Update state fields
        if "is_connected" in state_data:
            drone.is_connected = state_data["is_connected"]
        if "is_armed" in state_data:
            drone.is_armed = state_data["is_armed"]
        if "mode" in state_data:
            drone.mode = state_data["mode"]
        if "battery" in state_data:
            drone.battery = state_data["battery"]
        if "latitude" in state_data:
            drone.latitude = state_data["latitude"]
        if "longitude" in state_data:
            drone.longitude = state_data["longitude"]
        if "altitude" in state_data:
            drone.altitude = state_data["altitude"]
        if "roll" in state_data:
            drone.roll = state_data["roll"]
        if "pitch" in state_data:
            drone.pitch = state_data["pitch"]
        if "yaw" in state_data:
            drone.yaw = state_data["yaw"]
        if "landed" in state_data:
            drone.landed = state_data["landed"]
        if "reached" in state_data:
            drone.reached = state_data["reached"]
        if "returned" in state_data:
            drone.returned = state_data["returned"]
        if "tookoff" in state_data:
            drone.tookoff = state_data["tookoff"]
        
        drone.last_state_update = datetime.utcnow()
        drone.updated_at = datetime.utcnow()
        
        await db.commit()
        
        # Update cache (async, don't wait)
        asyncio.create_task(set_cache(f"drone:{drone_id}", drone, expire=60))
        
        return True

