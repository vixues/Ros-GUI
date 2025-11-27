"""Recording model for managing recordings."""
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class RecordingStatus(PyEnum):
    """Recording status enumeration."""
    IDLE = "idle"
    RECORDING = "recording"
    PAUSED = "paused"
    STOPPED = "stopped"
    SAVING = "saving"
    COMPLETED = "completed"
    ERROR = "error"


class Recording(Base):
    """Recording model for managing recordings."""
    
    __tablename__ = "recordings"
    
    id = Column(Integer, primary_key=True, index=True)
    drone_id = Column(Integer, ForeignKey("drones.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    status = Column(Enum(RecordingStatus), default=RecordingStatus.IDLE, nullable=False, index=True)
    
    # Recording configuration
    record_images = Column(Boolean, default=True, nullable=False)
    record_pointclouds = Column(Boolean, default=True, nullable=False)
    record_states = Column(Boolean, default=True, nullable=False)
    image_quality = Column(Integer, default=85, nullable=False)
    
    # File information
    file_path = Column(String(500), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Statistics
    image_count = Column(Integer, default=0, nullable=False)
    pointcloud_count = Column(Integer, default=0, nullable=False)
    state_count = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=True)
    stopped_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Metadata
    metadata = Column(JSON, nullable=True)  # Additional recording metadata
    
    # Relationships
    drone = relationship("Drone", back_populates="recordings")
    
    def __repr__(self) -> str:
        return f"<Recording(id={self.id}, name={self.name}, status={self.status.value}, drone_id={self.drone_id})>"

