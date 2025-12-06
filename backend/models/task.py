"""Task model."""
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ARRAY
from sqlalchemy.sql import func
from datetime import datetime
import enum

from ..database import Base


class TaskStatus(str, enum.Enum):
    """Task status enum."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class TaskPriority(str, enum.Enum):
    """Task priority enum."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Task(Base):
    """Task model for mission management."""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(
        Enum(TaskStatus),
        nullable=False,
        default=TaskStatus.PENDING,
        index=True
    )
    priority = Column(
        Enum(TaskPriority),
        nullable=False,
        default=TaskPriority.MEDIUM,
        index=True
    )
    assigned_drone_ids = Column(ARRAY(Integer), nullable=True, default=[])
    created_by = Column(Integer, nullable=False, index=True)
    updated_by = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    def __repr__(self):
        return f"<Task(id={self.id}, title={self.title}, status={self.status})>"

