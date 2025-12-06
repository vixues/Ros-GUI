"""Enhanced agent service with better error handling and LLM integration."""
import logging
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from ..models.agent import AgentSession, AgentAction
from ..schemas.agent import AgentSessionCreate, AgentMessage, AgentActionRequest
from ..config import settings

logger = logging.getLogger(__name__)


class AgentService:
    """Service for managing LLM agent sessions with enhanced error handling."""
    
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
        try:
            session = AgentSession(
                user_id=user_id,
                drone_id=session_data.drone_id,
                session_name=session_data.session_name,
                llm_model=session_data.llm_model or settings.LLM_MODEL,
                system_prompt=session_data.system_prompt,
                conversation_history=[],
                extra_metadata=session_data.extra_metadata if hasattr(session_data, 'extra_metadata') else getattr(session_data, 'metadata', None),
                is_active=True
            )
            db.add(session)
            await db.flush()
            await db.refresh(session)
            
            logger.info(f"Created agent session: {session.id} for user {user_id}")
            return session
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to create agent session: {e}")
            await db.rollback()
            raise
    
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
        try:
            result = await db.execute(
                select(AgentSession).where(AgentSession.id == session_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to retrieve session {session_id}: {e}")
            return None
    
    @staticmethod
    async def get_user_sessions(
        db: AsyncSession,
        user_id: int,
        include_inactive: bool = False
    ) -> List[AgentSession]:
        """
        Get all sessions for a user.
        
        Args:
            db: Database session
            user_id: User ID
            include_inactive: Include inactive sessions
            
        Returns:
            List of agent sessions
        """
        try:
            query = select(AgentSession).where(AgentSession.user_id == user_id)
            
            if not include_inactive:
                query = query.where(AgentSession.is_active == True)
            
            query = query.order_by(AgentSession.created_at.desc())
            
            result = await db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to retrieve user sessions: {e}")
            return []
    
    @staticmethod
    async def process_message(
        db: AsyncSession,
        session_id: int,
        message: AgentMessage
    ) -> Dict[str, Any]:
        """
        Process message through LLM agent.
        
        Args:
            db: Database session
            session_id: Session ID
            message: User message
            
        Returns:
            Agent response with action details
        """
        try:
            session = await AgentService.get_session(db, session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")
            
            if not session.is_active:
                raise ValueError(f"Session {session_id} is not active")
            
            # Create action record
            action = AgentAction(
                session_id=session_id,
                user_message=message.message,
                context=message.context,
                status="pending"
            )
            db.add(action)
            await db.flush()
            
            # Call LLM API with error handling
            try:
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
                
                # Limit history size
                if len(history) > 100:
                    history = history[-100:]
                
                session.conversation_history = history
                session.last_interaction_at = datetime.utcnow()
                
                await db.flush()
                await db.refresh(action)
                
                logger.info(f"Processed message in session {session_id}")
                
                return {
                    "response": agent_response.get("response", ""),
                    "command": agent_response.get("command"),
                    "result": agent_response.get("result"),
                    "action_id": action.id,
                    "type": agent_response.get("type", "text"),
                    "data": agent_response.get("data"),
                    "actions": agent_response.get("actions", [])
                }
                
            except Exception as llm_error:
                action.status = "failed"
                action.error_message = str(llm_error)
                action.executed_at = datetime.utcnow()
                await db.flush()
                
                logger.error(f"LLM processing error in session {session_id}: {llm_error}")
                raise
                
        except Exception as e:
            logger.error(f"Error processing message in session {session_id}: {e}")
            await db.rollback()
            raise
    
    @staticmethod
    async def _call_llm(
        session: AgentSession,
        user_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Call LLM API.
        
        Args:
            session: Agent session
            user_message: User message
            context: Additional context
            
        Returns:
            LLM response
        """
        # TODO: Implement actual LLM integration (OpenAI, Anthropic, etc.)
        # This is a placeholder implementation
        
        logger.info(f"Calling LLM for session {session.id}")
        
        # Mock response for now
        return {
            "response": f"Acknowledged: {user_message}. Standing by for further commands.",
            "command": None,
            "result": None,
            "type": "text",
            "data": None,
            "actions": []
        }
    
    @staticmethod
    async def end_session(db: AsyncSession, session_id: int) -> bool:
        """
        End agent session.
        
        Args:
            db: Database session
            session_id: Session ID
            
        Returns:
            True if successful
        """
        try:
            session = await AgentService.get_session(db, session_id)
            if not session:
                return False
            
            session.is_active = False
            session.ended_at = datetime.utcnow()
            
            await db.flush()
            
            logger.info(f"Ended agent session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to end session {session_id}: {e}")
            await db.rollback()
            return False
