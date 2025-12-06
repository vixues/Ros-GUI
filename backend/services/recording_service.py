"""Recording service for managing recordings."""
import logging
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.recording import Recording, RecordingStatus
from ..schemas.recording import RecordingCreate, RecordingUpdate

logger = logging.getLogger(__name__)


class RecordingService:
    """Service for managing recordings."""
    
    @staticmethod
    async def create_recording(db: AsyncSession, recording_data: RecordingCreate) -> Recording:
        """
        Create a new recording.
        
        Args:
            db: Database session
            recording_data: Recording creation data
            
        Returns:
            Created recording
        """
        recording = Recording(
            drone_id=recording_data.drone_id,
            name=recording_data.name,
            record_images=recording_data.record_images,
            record_pointclouds=recording_data.record_pointclouds,
            record_states=recording_data.record_states,
            image_quality=recording_data.image_quality,
            extra_metadata=recording_data.extra_metadata if hasattr(recording_data, 'extra_metadata') else getattr(recording_data, 'metadata', None),
            status=RecordingStatus.IDLE.value
        )
        db.add(recording)
        await db.commit()
        await db.refresh(recording)
        
        logger.info(f"Created recording: {recording.id} ({recording.name})")
        return recording
    
    @staticmethod
    async def get_recording(db: AsyncSession, recording_id: int) -> Optional[Recording]:
        """
        Get recording by ID.
        
        Args:
            db: Database session
            recording_id: Recording ID
            
        Returns:
            Recording or None
        """
        result = await db.execute(select(Recording).where(Recording.id == recording_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_recordings(
        db: AsyncSession,
        drone_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Recording]:
        """
        Get list of recordings.
        
        Args:
            db: Database session
            drone_id: Filter by drone ID
            skip: Skip records
            limit: Limit records
            
        Returns:
            List of recordings
        """
        query = select(Recording)
        
        if drone_id:
            query = query.where(Recording.drone_id == drone_id)
        
        query = query.offset(skip).limit(limit).order_by(Recording.created_at.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def update_recording(
        db: AsyncSession,
        recording_id: int,
        recording_data: RecordingUpdate
    ) -> Optional[Recording]:
        """
        Update recording.
        
        Args:
            db: Database session
            recording_id: Recording ID
            recording_data: Update data
            
        Returns:
            Updated recording or None
        """
        recording = await RecordingService.get_recording(db, recording_id)
        if not recording:
            return None
        
        update_data = recording_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(recording, key, value)
        
        recording.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(recording)
        
        logger.info(f"Updated recording: {recording_id}")
        return recording
    
    @staticmethod
    async def start_recording(db: AsyncSession, recording_id: int) -> Optional[Recording]:
        """
        Start recording.
        
        Args:
            db: Database session
            recording_id: Recording ID
            
        Returns:
            Updated recording or None
        """
        recording = await RecordingService.get_recording(db, recording_id)
        if not recording:
            return None
        
        recording.status = RecordingStatus.RECORDING.value
        recording.started_at = datetime.utcnow()
        recording.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(recording)
        
        logger.info(f"Started recording: {recording_id}")
        return recording
    
    @staticmethod
    async def stop_recording(db: AsyncSession, recording_id: int) -> Optional[Recording]:
        """
        Stop recording.
        
        Args:
            db: Database session
            recording_id: Recording ID
            
        Returns:
            Updated recording or None
        """
        recording = await RecordingService.get_recording(db, recording_id)
        if not recording:
            return None
        
        recording.status = RecordingStatus.STOPPED.value
        recording.stopped_at = datetime.utcnow()
        
        if recording.started_at:
            duration = (recording.stopped_at - recording.started_at).total_seconds()
            recording.duration_seconds = duration
        
        recording.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(recording)
        
        logger.info(f"Stopped recording: {recording_id}")
        return recording

