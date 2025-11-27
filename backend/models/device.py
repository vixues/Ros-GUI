"""Device model for managing hardware devices."""
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class DeviceType(PyEnum):
    """Device type enumeration."""
    DRONE = "drone"
    CAMERA = "camera"
    SENSOR = "sensor"
    GROUND_STATION = "ground_station"
    OTHER = "other"


class Device(Base):
    """Device model for managing hardware devices."""
    
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    device_type = Column(Enum(DeviceType), nullable=False, index=True)
    serial_number = Column(String(100), unique=True, nullable=True, index=True)
    manufacturer = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    firmware_version = Column(String(50), nullable=True)
    connection_url = Column(String(255), nullable=True)  # ROS bridge URL
    connection_config = Column(JSON, nullable=True)  # Additional connection config
    is_active = Column(Boolean, default=True, nullable=False)
    is_online = Column(Boolean, default=False, nullable=False)
    last_seen = Column(DateTime(timezone=True), nullable=True)
    metadata = Column(JSON, nullable=True)  # Additional device metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    drones = relationship("Drone", back_populates="device", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Device(id={self.id}, name={self.name}, type={self.device_type.value})>"

