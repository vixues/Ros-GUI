"""Agent service for LLM agent control."""
import logging
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.agent import AgentSession, AgentAction
from ..schemas.agent import AgentSessionCreate, AgentMessage, AgentActionRequest
from ..config import settings

logger = logging.getLogger(__name__)


class AgentService:
    """Service for managing LLM agent sessions."""
    
    @staticmethod
    async def create_session(
        db: AsyncSession,
        session_data: AgentSessionCreate,
        user_id: int
    ) -> AgentSession:
        """
        Create a new agent session.
        
        Args:
            db: Database session
            session_data: Session creation data
            user_id: User ID
            
        Returns:
            Created session
        """
        session = AgentSession(
            user_id=user_id,
            drone_id=session_data.drone_id,
            session_name=session_data.session_name,
            llm_model=session_data.llm_model or settings.LLM_MODEL,
            system_prompt=session_data.system_prompt,
            conversation_history=[],
            metadata=session_data.metadata,
            is_active=True
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        
        logger.info(f"Created agent session: {session.id} for user {user_id}")
        return session
    
    @staticmethod
    async def get_session(db: AsyncSession, session_id: int) -> Optional[AgentSession]:
        """
        Get agent session by ID.
        
        Args:
            db: Database session
            session_id: Session ID
            
        Returns:
            Agent session or None
        """
        result = await db.execute(
            select(AgentSession)
            .where(AgentSession.id == session_id)
            .options(selectinload(AgentSession.actions))
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_sessions(
        db: AsyncSession,
        user_id: int,
        active_only: bool = True
    ) -> List[AgentSession]:
        """
        Get user's agent sessions.
        
        Args:
            db: Database session
            user_id: User ID
            active_only: Only return active sessions
            
        Returns:
            List of sessions
        """
        query = select(AgentSession).where(AgentSession.user_id == user_id)
        
        if active_only:
            query = query.where(AgentSession.is_active == True)
        
        query = query.order_by(AgentSession.started_at.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def process_message(
        db: AsyncSession,
        session_id: int,
        message: AgentMessage
    ) -> Dict[str, Any]:
        """
        Process user message and generate agent response.
        
        Args:
            db: Database session
            session_id: Session ID
            message: User message
            
        Returns:
            Agent response
        """
        session = await AgentService.get_session(db, session_id)
        if not session or not session.is_active:
            raise ValueError("Session not found or inactive")
        
        # Create action record
        action = AgentAction(
            session_id=session_id,
            action_type="message",
            user_message=message.message,
            status="pending"
        )
        db.add(action)
        await db.flush()
        
        try:
            # Call LLM API (placeholder - implement actual LLM integration)
            agent_response = await AgentService._call_llm(
                session, message.message, message.context
            )
            
            action.agent_response = agent_response.get("response", "")
            action.executed_command = agent_response.get("command")
            action.command_result = agent_response.get("result")
            action.status = "success"
            action.executed_at = datetime.utcnow()
            
            # Update conversation history
            history = session.conversation_history or []
            history.append({
                "role": "user",
                "content": message.message,
                "timestamp": datetime.utcnow().isoformat()
            })
            history.append({
                "role": "assistant",
                "content": agent_response.get("response", ""),
                "timestamp": datetime.utcnow().isoformat()
            })
            session.conversation_history = history
            session.last_interaction_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(action)
            
            logger.info(f"Processed message in session {session_id}")
            
            return {
                "response": agent_response.get("response", ""),
                "command": agent_response.get("command"),
                "result": agent_response.get("result"),
                "action_id": action.id
            }
        except Exception as e:
            action.status = "failed"
            action.error_message = str(e)
            action.executed_at = datetime.utcnow()
            await db.commit()
            
            logger.error(f"Error processing message: {e}")
            raise
    
    @staticmethod
    async def _call_llm(
        session: AgentSession,
        user_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Call LLM API (placeholder implementation).
        
        Args:
            session: Agent session
            user_message: User message
            context: Additional context
            
        Returns:
            LLM response
        """
        if not settings.LLM_ENABLED:
            return {
                "response": "LLM agent is disabled. Please enable it in configuration.",
                "command": None,
                "result": None
            }
        
        # TODO: Implement actual LLM API call
        # This is a placeholder that should be replaced with actual LLM integration
        # (e.g., OpenAI, Anthropic, local LLM, etc.)
        
        logger.warning("LLM API call not implemented - using placeholder")
        
        return {
            "response": f"Received message: {user_message}. LLM integration pending.",
            "command": None,
            "result": None
        }
    
    @staticmethod
    async def end_session(db: AsyncSession, session_id: int) -> Optional[AgentSession]:
        """
        End agent session.
        
        Args:
            db: Database session
            session_id: Session ID
            
        Returns:
            Updated session or None
        """
        session = await AgentService.get_session(db, session_id)
        if not session:
            return None
        
        session.is_active = False
        session.ended_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(session)
        
        logger.info(f"Ended agent session: {session_id}")
        return session

