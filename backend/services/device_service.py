"""Device service for managing devices."""
import logging
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.device import Device
from ..schemas.device import DeviceCreate, DeviceUpdate
from ..cache import get_cache, set_cache, delete_cache

logger = logging.getLogger(__name__)


class DeviceService:
    """Service for managing devices."""
    
    @staticmethod
    async def create_device(db: AsyncSession, device_data: DeviceCreate) -> Device:
        """
        Create a new device.
        
        Args:
            db: Database session
            device_data: Device creation data
            
        Returns:
            Created device
        """
        device = Device(
            name=device_data.name,
            device_type=device_data.device_type,
            serial_number=device_data.serial_number,
            manufacturer=device_data.manufacturer,
            model=device_data.model,
            firmware_version=device_data.firmware_version,
            connection_url=device_data.connection_url,
            connection_config=device_data.connection_config,
            extra_metadata=device_data.extra_metadata if hasattr(device_data, 'extra_metadata') else getattr(device_data, 'metadata', None)
        )
        db.add(device)
        await db.commit()
        await db.refresh(device)
        
        # Clear cache
        await delete_cache("devices:list")
        
        logger.info(f"Created device: {device.id} ({device.name})")
        return device
    
    @staticmethod
    async def get_device(db: AsyncSession, device_id: int) -> Optional[Device]:
        """
        Get device by ID.
        
        Args:
            db: Database session
            device_id: Device ID
            
        Returns:
            Device or None
        """
        # Try cache first
        cache_key = f"device:{device_id}"
        cached = await get_cache(cache_key)
        if cached:
            return cached
        
        result = await db.execute(select(Device).where(Device.id == device_id))
        device = result.scalar_one_or_none()
        
        if device:
            await set_cache(cache_key, device, expire=60)
        
        return device
    
    @staticmethod
    async def get_devices(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        device_type: Optional[str] = None
    ) -> List[Device]:
        """
        Get list of devices.
        
        Args:
            db: Database session
            skip: Skip records
            limit: Limit records
            device_type: Filter by device type
            
        Returns:
            List of devices
        """
        query = select(Device)
        
        if device_type:
            query = query.where(Device.device_type == device_type)
        
        query = query.offset(skip).limit(limit).order_by(Device.created_at.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def update_device(
        db: AsyncSession,
        device_id: int,
        device_data: DeviceUpdate
    ) -> Optional[Device]:
        """
        Update device.
        
        Args:
            db: Database session
            device_id: Device ID
            device_data: Update data
            
        Returns:
            Updated device or None
        """
        device = await DeviceService.get_device(db, device_id)
        if not device:
            return None
        
        update_data = device_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(device, key, value)
        
        device.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(device)
        
        # Clear cache
        await delete_cache(f"device:{device_id}")
        await delete_cache("devices:list")
        
        logger.info(f"Updated device: {device_id}")
        return device
    
    @staticmethod
    async def delete_device(db: AsyncSession, device_id: int) -> bool:
        """
        Delete device.
        
        Args:
            db: Database session
            device_id: Device ID
            
        Returns:
            True if deletion successful
        """
        device = await DeviceService.get_device(db, device_id)
        if not device:
            return False
        
        await db.delete(device)
        await db.commit()
        
        # Clear cache
        await delete_cache(f"device:{device_id}")
        await delete_cache("devices:list")
        
        logger.info(f"Deleted device: {device_id}")
        return True

