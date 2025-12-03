"""
工具调用相关类型定义

定义工具调用的请求、响应和状态等数据结构。
"""

from enum import Enum
from typing import Optional, Dict, List, Any, Callable, Awaitable, Union
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from .task_state import ToolCallStatus


class ToolType(Enum):
    """工具类型"""
    
    NORMAL = "normal"              # 普通工具
    MODIFICATION = "modification"  # 修改类工具（需确认）
    DANGEROUS = "dangerous"        # 危险操作（必须确认）
    SUBAGENT = "subagent"         # 子代理工具


class ToolConfirmationOutcome(Enum):
    """工具确认结果"""
    
    PROCEED_ONCE = "proceed_once"           # 本次执行
    CANCEL = "cancel"                        # 取消执行
    PROCEED_ALWAYS = "proceed_always"        # 总是执行（当前会话）
    PROCEED_ALWAYS_TOOL = "proceed_always_tool"  # 该工具总是执行
    MODIFY = "modify"                        # 修改参数后执行


@dataclass
class ToolSchema:
    """工具 Schema 定义"""
    
    name: str
    description: str
    parameters: Dict[str, Any]
    required: List[str] = field(default_factory=list)
    returns: Optional[Dict[str, Any]] = None
    dangerous: bool = False
    confirmation_required: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "required": self.required,
            "returns": self.returns,
            "dangerous": self.dangerous,
            "confirmation_required": self.confirmation_required,
        }
    
    def to_openai_format(self) -> Dict[str, Any]:
        """转换为 OpenAI function calling 格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters,
                    "required": self.required,
                },
            },
        }


@dataclass
class ToolCallRequest:
    """工具调用请求"""
    
    call_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    args: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "call_id": self.call_id,
            "name": self.name,
            "args": self.args,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ToolResult:
    """工具执行结果"""
    
    call_id: str = ""
    success: bool = True
    # 返回给 LLM 的内容
    llm_content: List[Dict[str, Any]] = field(default_factory=list)
    # 显示给用户的内容
    display_content: Optional[str] = None
    # 原始返回数据
    raw_data: Optional[Any] = None
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    # 错误信息
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "call_id": self.call_id,
            "success": self.success,
            "llm_content": self.llm_content,
            "display_content": self.display_content,
            "raw_data": self.raw_data,
            "metadata": self.metadata,
            "error": self.error,
        }
    
    @classmethod
    def success_result(
        cls,
        call_id: str,
        content: str,
        display: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "ToolResult":
        """创建成功结果"""
        return cls(
            call_id=call_id,
            success=True,
            llm_content=[{"type": "text", "text": content}],
            display_content=display or content,
            metadata=metadata or {},
        )
    
    @classmethod
    def error_result(
        cls,
        call_id: str,
        error: str,
        display: Optional[str] = None,
    ) -> "ToolResult":
        """创建错误结果"""
        return cls(
            call_id=call_id,
            success=False,
            llm_content=[{"type": "text", "text": f"Error: {error}"}],
            display_content=display or f"❌ {error}",
            error=error,
        )


@dataclass
class ToolConfirmationDetails:
    """工具确认详情"""
    
    type: str  # normal, dangerous, modification
    tool_name: str
    args: Dict[str, Any]
    description: Optional[str] = None
    on_confirm: Optional[Callable[[ToolConfirmationOutcome, Optional[Dict[str, Any]]], Awaitable[None]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "tool_name": self.tool_name,
            "args": self.args,
            "description": self.description,
        }


@dataclass
class ToolCall:
    """工具调用状态"""
    
    request: ToolCallRequest
    status: ToolCallStatus = ToolCallStatus.SCHEDULED
    tool_type: ToolType = ToolType.NORMAL
    confirmation_details: Optional[ToolConfirmationDetails] = None
    result: Optional[ToolResult] = None
    live_output: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "request": self.request.to_dict(),
            "status": self.status.value,
            "tool_type": self.tool_type.value,
            "live_output": self.live_output,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
        if self.confirmation_details:
            result["confirmation_details"] = self.confirmation_details.to_dict()
        if self.result:
            result["result"] = self.result.to_dict()
        return result


@dataclass
class CompletedToolCall:
    """已完成的工具调用"""
    
    request: ToolCallRequest
    result: ToolResult
    duration_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "request": self.request.to_dict(),
            "result": self.result.to_dict(),
            "duration_ms": self.duration_ms,
        }


# Type aliases for LLM response parts
LLMContentPart = Union[Dict[str, Any], str]
LLMContent = List[LLMContentPart]

