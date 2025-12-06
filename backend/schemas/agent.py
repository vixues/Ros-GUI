"""Agent schemas."""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


class AgentSessionCreate(BaseModel):
    """Agent session creation request model."""
    drone_id: Optional[int] = Field(None, description="Drone ID")
    session_name: Optional[str] = Field(None, max_length=255, description="Session name")
    llm_model: Optional[str] = Field(None, max_length=100, description="LLM model")
    system_prompt: Optional[str] = Field(None, description="System prompt")
    extra_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata", alias="metadata")


class AgentMessage(BaseModel):
    """Agent message model."""
    message: str = Field(..., min_length=1, description="User message")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class AgentActionRequest(BaseModel):
    """Agent action request model."""
    action_type: str = Field(..., description="Action type")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Action parameters")


class AgentActionResponse(BaseModel):
    """Agent action response model."""
    id: int
    session_id: int
    action_type: str
    user_message: Optional[str]
    agent_response: Optional[str]
    executed_command: Optional[str]
    command_result: Optional[Dict[str, Any]]
    status: str
    error_message: Optional[str]
    created_at: datetime
    executed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class AgentSessionResponse(BaseModel):
    """Agent session response model."""
    id: int
    user_id: int
    drone_id: Optional[int]
    session_name: Optional[str]
    is_active: bool
    llm_model: Optional[str]
    started_at: datetime
    ended_at: Optional[datetime]
    last_interaction_at: Optional[datetime]
    actions: List[AgentActionResponse] = []
    
    class Config:
        from_attributes = True

