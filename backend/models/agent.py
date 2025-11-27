"""Agent model for LLM agent control."""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class AgentSession(Base):
    """Agent session model for LLM agent control sessions."""
    
    __tablename__ = "agent_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    drone_id = Column(Integer, ForeignKey("drones.id"), nullable=True, index=True)
    session_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # LLM configuration
    llm_model = Column(String(100), nullable=True)
    system_prompt = Column(Text, nullable=True)
    conversation_history = Column(JSON, nullable=True)  # Store conversation history
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    last_interaction_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)  # Additional session metadata
    
    # Relationships
    user = relationship("User", back_populates="agent_sessions")
    actions = relationship("AgentAction", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<AgentSession(id={self.id}, user_id={self.user_id}, drone_id={self.drone_id}, is_active={self.is_active})>"


class AgentAction(Base):
    """Agent action model for recording agent actions."""
    
    __tablename__ = "agent_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("agent_sessions.id"), nullable=False, index=True)
    
    # Action details
    action_type = Column(String(50), nullable=False, index=True)  # e.g., "command", "query", "control"
    user_message = Column(Text, nullable=True)  # User's message/request
    agent_response = Column(Text, nullable=True)  # Agent's response
    executed_command = Column(Text, nullable=True)  # Command executed by agent
    command_result = Column(JSON, nullable=True)  # Result of command execution
    
    # Status
    status = Column(String(20), default="pending", nullable=False)  # pending, success, failed
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)  # Additional action metadata
    
    # Relationships
    session = relationship("AgentSession", back_populates="actions")
    
    def __repr__(self) -> str:
        return f"<AgentAction(id={self.id}, session_id={self.session_id}, action_type={self.action_type}, status={self.status})>"

