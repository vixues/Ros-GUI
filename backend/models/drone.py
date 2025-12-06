"""Drone model for managing multiple drones."""
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class DroneStatus(PyEnum):
    """Drone status enumeration."""
    IDLE = "idle"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ARMED = "armed"
    FLYING = "flying"
    LANDING = "landing"
    LANDED = "landed"
    ERROR = "error"
    DISCONNECTED = "disconnected"


class Drone(Base):
    """Drone model for managing multiple drones."""
    
    __tablename__ = "drones"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True, index=True)
    drone_id = Column(String(50), unique=True, nullable=False, index=True)  # Unique drone identifier
    status = Column(String(20), default=DroneStatus.IDLE.value, nullable=False, index=True)
    
    # Connection info
    connection_url = Column(String(255), nullable=True)  # ROS bridge URL
    use_mock = Column(Boolean, default=False, nullable=False)
    mock_config = Column(JSON, nullable=True)
    
    # State information (latest snapshot)
    is_connected = Column(Boolean, default=False, nullable=False)
    is_armed = Column(Boolean, default=False, nullable=False)
    mode = Column(String(50), nullable=True)
    battery = Column(Float, default=100.0, nullable=False)
    
    # Position
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    altitude = Column(Float, nullable=True)
    
    # Orientation
    roll = Column(Float, nullable=True)
    pitch = Column(Float, nullable=True)
    yaw = Column(Float, nullable=True)
    
    # Flight state
    landed = Column(Boolean, default=True, nullable=False)
    reached = Column(Boolean, default=False, nullable=False)
    returned = Column(Boolean, default=False, nullable=False)
    tookoff = Column(Boolean, default=False, nullable=False)
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)  # Additional drone metadata
    last_state_update = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    device = relationship("Device", back_populates="drones")
    operations = relationship("Operation", back_populates="drone", cascade="all, delete-orphan")
    connections = relationship("DroneConnection", back_populates="drone", cascade="all, delete-orphan")
    recordings = relationship("Recording", back_populates="drone", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Drone(id={self.id}, name={self.name}, drone_id={self.drone_id}, status={self.status})>"


class DroneConnection(Base):
    """Drone connection history."""
    
    __tablename__ = "drone_connections"
    
    id = Column(Integer, primary_key=True, index=True)
    drone_id = Column(Integer, ForeignKey("drones.id"), nullable=False, index=True)
    connection_url = Column(String(255), nullable=False)
    connected_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    disconnected_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Float, nullable=True)
    disconnect_reason = Column(Text, nullable=True)
    
    # Relationships
    drone = relationship("Drone", back_populates="connections")
    
    def __repr__(self) -> str:
        return f"<DroneConnection(id={self.id}, drone_id={self.drone_id}, connected_at={self.connected_at})>"

