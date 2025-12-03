"""
消息类型定义模块

定义系统中使用的各类消息格式。
"""

from enum import Enum
from typing import Optional, Dict, List, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
import uuid


class MessageRole(Enum):
    """消息角色"""
    
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class ContentType(Enum):
    """内容类型"""
    
    TEXT = "text"
    IMAGE = "image"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    THOUGHT = "thought"
    DATA = "data"


@dataclass
class MessagePart:
    """消息部分"""
    
    type: ContentType
    content: Any
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "type": self.type.value,
            "content": self.content,
        }
        if self.metadata:
            result["metadata"] = self.metadata
        return result
    
    @classmethod
    def text(cls, text: str) -> "MessagePart":
        """创建文本消息部分"""
        return cls(type=ContentType.TEXT, content=text)
    
    @classmethod
    def thought(cls, thought: str, subject: Optional[str] = None) -> "MessagePart":
        """创建思考消息部分"""
        return cls(
            type=ContentType.THOUGHT,
            content=thought,
            metadata={"subject": subject} if subject else None,
        )


@dataclass
class Message:
    """消息"""
    
    role: MessageRole
    parts: List[MessagePart]
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    task_id: Optional[str] = None
    context_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role.value,
            "parts": [p.to_dict() for p in self.parts],
            "message_id": self.message_id,
            "timestamp": self.timestamp.isoformat(),
            "task_id": self.task_id,
            "context_id": self.context_id,
            "metadata": self.metadata,
        }
    
    @classmethod
    def user_message(cls, text: str, **kwargs) -> "Message":
        """创建用户消息"""
        return cls(
            role=MessageRole.USER,
            parts=[MessagePart.text(text)],
            **kwargs,
        )
    
    @classmethod
    def assistant_message(cls, text: str, **kwargs) -> "Message":
        """创建助手消息"""
        return cls(
            role=MessageRole.ASSISTANT,
            parts=[MessagePart.text(text)],
            **kwargs,
        )
    
    @classmethod
    def system_message(cls, text: str, **kwargs) -> "Message":
        """创建系统消息"""
        return cls(
            role=MessageRole.SYSTEM,
            parts=[MessagePart.text(text)],
            **kwargs,
        )
    
    @property
    def text_content(self) -> str:
        """获取纯文本内容"""
        texts = []
        for part in self.parts:
            if part.type == ContentType.TEXT:
                texts.append(str(part.content))
        return "\n".join(texts)


@dataclass
class ConversationContext:
    """对话上下文"""
    
    context_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[Message] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_message(self, message: Message) -> None:
        """添加消息"""
        message.context_id = self.context_id
        self.messages.append(message)
        self.updated_at = datetime.now()
    
    def get_history(self, limit: Optional[int] = None) -> List[Message]:
        """获取历史消息"""
        if limit:
            return self.messages[-limit:]
        return self.messages
    
    def to_llm_format(self) -> List[Dict[str, Any]]:
        """转换为LLM格式"""
        result = []
        for msg in self.messages:
            llm_msg = {
                "role": msg.role.value,
                "content": msg.text_content,
            }
            result.append(llm_msg)
        return result


@dataclass  
class ThoughtSummary:
    """思考摘要"""
    
    subject: Optional[str] = None
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "subject": self.subject,
            "description": self.description,
        }

