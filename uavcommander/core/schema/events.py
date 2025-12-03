"""
事件类型定义模块

定义系统中使用的各类事件格式，用于 EventBus 通信。
"""

from enum import Enum
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from .task_state import TaskState, ToolCallStatus


class EventType(Enum):
    """事件类型枚举"""
    
    # 任务相关事件
    TASK_CREATED = "task_created"
    TASK_STATE_CHANGE = "task_state_change"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    
    # 工具调用事件
    TOOL_CALL_SCHEDULED = "tool_call_scheduled"
    TOOL_CALL_STARTED = "tool_call_started"
    TOOL_CALL_COMPLETED = "tool_call_completed"
    TOOL_CALL_FAILED = "tool_call_failed"
    TOOL_CALL_CONFIRMATION = "tool_call_confirmation"
    
    # 内容输出事件
    TEXT_CONTENT = "text_content"
    THOUGHT_CHUNK = "thought_chunk"
    STREAM_CHUNK = "stream_chunk"
    
    # Agent 相关事件
    AGENT_STARTED = "agent_started"
    AGENT_FINISHED = "agent_finished"
    SUBAGENT_INVOKED = "subagent_invoked"
    SUBAGENT_COMPLETED = "subagent_completed"
    
    # 系统事件
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class BaseEvent:
    """事件基类"""
    
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.INFO
    timestamp: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "metadata": self.metadata,
        }


@dataclass
class TaskEvent(BaseEvent):
    """任务事件"""
    
    task_id: str = ""
    context_id: str = ""
    state: Optional[TaskState] = None
    message: Optional[str] = None
    final: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update({
            "task_id": self.task_id,
            "context_id": self.context_id,
            "state": self.state.value if self.state else None,
            "message": self.message,
            "final": self.final,
        })
        return result


@dataclass
class TaskStatusUpdateEvent(TaskEvent):
    """任务状态更新事件"""
    
    event_type: EventType = EventType.TASK_STATE_CHANGE
    status: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result["status"] = self.status
        return result


@dataclass
class ToolCallEvent(BaseEvent):
    """工具调用事件"""
    
    call_id: str = ""
    tool_name: str = ""
    task_id: str = ""
    status: Optional[ToolCallStatus] = None
    args: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update({
            "call_id": self.call_id,
            "tool_name": self.tool_name,
            "task_id": self.task_id,
            "status": self.status.value if self.status else None,
            "args": self.args,
            "result": self.result,
            "error": self.error,
        })
        return result


@dataclass
class ToolConfirmationEvent(ToolCallEvent):
    """工具确认事件"""
    
    event_type: EventType = EventType.TOOL_CALL_CONFIRMATION
    confirmation_type: str = "normal"  # normal, dangerous, modification
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update({
            "confirmation_type": self.confirmation_type,
            "description": self.description,
        })
        return result


@dataclass
class ContentEvent(BaseEvent):
    """内容输出事件"""
    
    task_id: str = ""
    content: str = ""
    content_type: str = "text"  # text, thought, code
    is_streaming: bool = False
    is_final: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update({
            "task_id": self.task_id,
            "content": self.content,
            "content_type": self.content_type,
            "is_streaming": self.is_streaming,
            "is_final": self.is_final,
        })
        return result


@dataclass
class ThoughtEvent(ContentEvent):
    """思考事件"""
    
    event_type: EventType = EventType.THOUGHT_CHUNK
    content_type: str = "thought"
    subject: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result["subject"] = self.subject
        return result


@dataclass
class AgentActivityEvent(BaseEvent):
    """Agent 活动事件"""
    
    agent_name: str = ""
    agent_type: str = ""  # coordinator, specialist, subagent
    activity: str = ""
    task_id: str = ""
    parent_agent: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update({
            "agent_name": self.agent_name,
            "agent_type": self.agent_type,
            "activity": self.activity,
            "task_id": self.task_id,
            "parent_agent": self.parent_agent,
        })
        return result


@dataclass
class ErrorEvent(BaseEvent):
    """错误事件"""
    
    event_type: EventType = EventType.ERROR
    error_code: Optional[str] = None
    error_message: str = ""
    task_id: Optional[str] = None
    recoverable: bool = False
    stack_trace: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update({
            "error_code": self.error_code,
            "error_message": self.error_message,
            "task_id": self.task_id,
            "recoverable": self.recoverable,
            "stack_trace": self.stack_trace,
        })
        return result

