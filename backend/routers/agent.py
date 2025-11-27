"""Agent routes for LLM agent control."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..auth import get_current_active_user
from ..models.user import User
from ..schemas.agent import (
    AgentSessionCreate,
    AgentSessionResponse,
    AgentMessage,
    AgentActionResponse
)
from ..schemas.response import ResponseModel
from ..services.agent_service import AgentService

router = APIRouter(prefix="/api/agent", tags=["Agent"])


@router.post("/sessions", response_model=ResponseModel[AgentSessionResponse], status_code=status.HTTP_201_CREATED)
async def create_agent_session(
    session_data: AgentSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new agent session."""
    session = await AgentService.create_session(db, session_data, current_user.id)
    return ResponseModel(
        status=status.HTTP_201_CREATED,
        message="Agent session created successfully",
        data=AgentSessionResponse.model_validate(session)
    )


@router.get("/sessions", response_model=ResponseModel[List[AgentSessionResponse]])
async def get_agent_sessions(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user's agent sessions."""
    sessions = await AgentService.get_user_sessions(db, current_user.id, active_only=active_only)
    return ResponseModel(
        status=status.HTTP_200_OK,
        message="Agent sessions retrieved successfully",
        data=[AgentSessionResponse.model_validate(session) for session in sessions]
    )


@router.get("/sessions/{session_id}", response_model=ResponseModel[AgentSessionResponse])
async def get_agent_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get agent session by ID."""
    session = await AgentService.get_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent session not found"
        )
    
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return ResponseModel(
        status=status.HTTP_200_OK,
        message="Agent session retrieved successfully",
        data=AgentSessionResponse.model_validate(session)
    )


@router.post("/sessions/{session_id}/message", response_model=ResponseModel[dict])
async def send_agent_message(
    session_id: int,
    message: AgentMessage,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Send message to agent and get response."""
    session = await AgentService.get_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent session not found"
        )
    
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        response = await AgentService.process_message(db, session_id, message)
        return ResponseModel(
            status=status.HTTP_200_OK,
            message="Message processed successfully",
            data=response
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing message: {str(e)}"
        )


@router.post("/sessions/{session_id}/end", response_model=ResponseModel[AgentSessionResponse])
async def end_agent_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """End agent session."""
    session = await AgentService.get_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent session not found"
        )
    
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    session = await AgentService.end_session(db, session_id)
    return ResponseModel(
        status=status.HTTP_200_OK,
        message="Agent session ended successfully",
        data=AgentSessionResponse.model_validate(session)
    )

