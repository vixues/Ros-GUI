"""System log model."""
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, JSON
from sqlalchemy.sql import func
import enum

from ..database import Base


class LogLevel(str, enum.Enum):
    """Log level enum."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    SUCCESS = "SUCCESS"


class SystemLog(Base):
    """System log model."""
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    level = Column(Enum(LogLevel), nullable=False, index=True)
    module = Column(String(100), nullable=False, index=True)
    message = Column(Text, nullable=False)
    extra_metadata = Column(JSON, nullable=True)
    user_id = Column(Integer, nullable=True, index=True)

    def __repr__(self):
        return f"<SystemLog(id={self.id}, level={self.level}, module={self.module})>"

