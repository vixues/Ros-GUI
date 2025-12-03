"""
Schema 模块

定义系统中使用的所有数据模式和类型。
"""

from .task_state import (
    TaskState,
    ToolCallStatus,
    TaskStateTransition,
    VALID_TRANSITIONS,
    is_valid_transition,
    is_terminal_state,
)

from .messages import (
    MessageRole,
    ContentType,
    MessagePart,
    Message,
    ConversationContext,
    ThoughtSummary,
)

from .events import (
    EventType,
    BaseEvent,
    TaskEvent,
    TaskStatusUpdateEvent,
    ToolCallEvent,
    ToolConfirmationEvent,
    ContentEvent,
    ThoughtEvent,
    AgentActivityEvent,
    ErrorEvent,
)

from .tool_call import (
    ToolType,
    ToolConfirmationOutcome,
    ToolSchema,
    ToolCallRequest,
    ToolResult,
    ToolConfirmationDetails,
    ToolCall,
    CompletedToolCall,
    LLMContentPart,
    LLMContent,
)


__all__ = [
    # task_state
    "TaskState",
    "ToolCallStatus",
    "TaskStateTransition",
    "VALID_TRANSITIONS",
    "is_valid_transition",
    "is_terminal_state",
    # messages
    "MessageRole",
    "ContentType",
    "MessagePart",
    "Message",
    "ConversationContext",
    "ThoughtSummary",
    # events
    "EventType",
    "BaseEvent",
    "TaskEvent",
    "TaskStatusUpdateEvent",
    "ToolCallEvent",
    "ToolConfirmationEvent",
    "ContentEvent",
    "ThoughtEvent",
    "AgentActivityEvent",
    "ErrorEvent",
    # tool_call
    "ToolType",
    "ToolConfirmationOutcome",
    "ToolSchema",
    "ToolCallRequest",
    "ToolResult",
    "ToolConfirmationDetails",
    "ToolCall",
    "CompletedToolCall",
    "LLMContentPart",
    "LLMContent",
]

