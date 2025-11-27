"""Operation model for recording all operations."""
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class OperationType(PyEnum):
    """Operation type enumeration."""
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    ARM = "arm"
    DISARM = "disarm"
    TAKEOFF = "takeoff"
    LAND = "land"
    SET_MODE = "set_mode"
    PUBLISH = "publish"
    SERVICE_CALL = "service_call"
    WAYPOINT = "waypoint"
    RETURN_TO_HOME = "return_to_home"
    EMERGENCY_STOP = "emergency_stop"
    RECORDING_START = "recording_start"
    RECORDING_STOP = "recording_stop"
    AGENT_ACTION = "agent_action"
    OTHER = "other"


class OperationStatus(PyEnum):
    """Operation status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Operation(Base):
    """Operation model for recording all operations."""
    
    __tablename__ = "operations"
    
    id = Column(Integer, primary_key=True, index=True)
    operation_type = Column(Enum(OperationType), nullable=False, index=True)
    status = Column(Enum(OperationStatus), default=OperationStatus.PENDING, nullable=False, index=True)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    drone_id = Column(Integer, ForeignKey("drones.id"), nullable=True, index=True)
    
    # Operation details
    topic = Column(String(255), nullable=True)  # For publish operations
    service_name = Column(String(255), nullable=True)  # For service calls
    payload = Column(JSON, nullable=True)  # Operation payload
    response = Column(JSON, nullable=True)  # Operation response
    error_message = Column(Text, nullable=True)  # Error message if failed
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)  # Additional operation metadata
    
    # Relationships
    user = relationship("User", back_populates="operations")
    drone = relationship("Drone", back_populates="operations")
    
    def __repr__(self) -> str:
        return f"<Operation(id={self.id}, type={self.operation_type.value}, status={self.status.value}, drone_id={self.drone_id})>"

