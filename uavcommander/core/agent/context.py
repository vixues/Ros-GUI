"""
上下文管理模块

管理对话历史、上下文压缩和多任务隔离。
"""

import asyncio
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import json
import logging

from core.schema import Message, MessageRole, ConversationContext

logger = logging.getLogger(__name__)


@dataclass
class ContextConfig:
    """上下文配置"""
    
    # 最大历史消息数
    max_messages: int = 100
    # 最大 token 数（用于压缩）
    max_tokens: int = 8000
    # 是否启用自动压缩
    auto_compress: bool = True
    # 压缩阈值（token 数）
    compress_threshold: int = 6000
    # 保留的最近消息数（压缩时）
    preserve_recent: int = 10


@dataclass
class ContextSummary:
    """上下文摘要"""
    
    summary: str
    key_points: List[str] = field(default_factory=list)
    entities: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class Context:
    """上下文管理器"""
    
    def __init__(
        self,
        context_id: Optional[str] = None,
        config: Optional[ContextConfig] = None,
    ):
        self.context_id = context_id or str(uuid.uuid4())
        self.config = config or ContextConfig()
        
        self._conversation = ConversationContext(context_id=self.context_id)
        self._summaries: List[ContextSummary] = []
        self._metadata: Dict[str, Any] = {}
        self._token_count: int = 0
    
    @property
    def messages(self) -> List[Message]:
        """获取消息列表"""
        return self._conversation.messages
    
    @property
    def message_count(self) -> int:
        """消息数量"""
        return len(self._conversation.messages)
    
    def add_message(self, message: Message) -> None:
        """添加消息"""
        self._conversation.add_message(message)
        self._token_count += self._estimate_tokens(message)
        
        # 检查是否需要压缩
        if (
            self.config.auto_compress and
            self._token_count > self.config.compress_threshold
        ):
            self._compress()
    
    def add_user_message(self, content: str) -> Message:
        """添加用户消息"""
        message = Message.user_message(content, context_id=self.context_id)
        self.add_message(message)
        return message
    
    def add_assistant_message(self, content: str) -> Message:
        """添加助手消息"""
        message = Message.assistant_message(content, context_id=self.context_id)
        self.add_message(message)
        return message
    
    def add_system_message(self, content: str) -> Message:
        """添加系统消息"""
        message = Message.system_message(content, context_id=self.context_id)
        self.add_message(message)
        return message
    
    def get_history(
        self,
        limit: Optional[int] = None,
        include_system: bool = True,
    ) -> List[Message]:
        """获取历史消息"""
        messages = self._conversation.get_history(limit)
        
        if not include_system:
            messages = [m for m in messages if m.role != MessageRole.SYSTEM]
        
        return messages
    
    def get_llm_messages(self) -> List[Dict[str, Any]]:
        """获取 LLM 格式的消息"""
        messages = []
        
        # 添加摘要（如果有）
        if self._summaries:
            summary_text = self._format_summaries()
            messages.append({
                "role": "system",
                "content": f"[历史摘要]\n{summary_text}",
            })
        
        # 添加对话消息
        messages.extend(self._conversation.to_llm_format())
        
        return messages
    
    def set_metadata(self, key: str, value: Any) -> None:
        """设置元数据"""
        self._metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据"""
        return self._metadata.get(key, default)
    
    def clear(self) -> None:
        """清空上下文"""
        self._conversation = ConversationContext(context_id=self.context_id)
        self._summaries.clear()
        self._token_count = 0
    
    def _estimate_tokens(self, message: Message) -> int:
        """估算消息的 token 数"""
        # 简单估算：每4个字符约1个token
        text = message.text_content
        return len(text) // 4 + 1
    
    def _compress(self) -> None:
        """压缩上下文"""
        if self.message_count <= self.config.preserve_recent:
            return
        
        logger.info(f"[Context] 压缩上下文: {self.message_count} 条消息")
        
        # 获取需要压缩的消息
        messages_to_compress = self.messages[:-self.config.preserve_recent]
        
        # 生成摘要
        summary = self._generate_summary(messages_to_compress)
        self._summaries.append(summary)
        
        # 保留最近的消息
        self._conversation.messages = self.messages[-self.config.preserve_recent:]
        
        # 重新计算 token
        self._token_count = sum(
            self._estimate_tokens(m) for m in self._conversation.messages
        )
        
        logger.info(f"[Context] 压缩后: {self.message_count} 条消息")
    
    def _generate_summary(self, messages: List[Message]) -> ContextSummary:
        """生成消息摘要"""
        # 简单实现：提取关键内容
        key_points = []
        
        for msg in messages:
            content = msg.text_content
            if len(content) > 100:
                key_points.append(content[:100] + "...")
            else:
                key_points.append(content)
        
        summary_text = "对话包含以下要点：\n" + "\n".join(
            f"- {p}" for p in key_points[:5]
        )
        
        return ContextSummary(
            summary=summary_text,
            key_points=key_points[:5],
        )
    
    def _format_summaries(self) -> str:
        """格式化摘要"""
        parts = []
        for i, summary in enumerate(self._summaries, 1):
            parts.append(f"摘要 {i}:\n{summary.summary}")
        return "\n\n".join(parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "context_id": self.context_id,
            "messages": [m.to_dict() for m in self.messages],
            "summaries": [
                {
                    "summary": s.summary,
                    "key_points": s.key_points,
                    "timestamp": s.timestamp.isoformat(),
                }
                for s in self._summaries
            ],
            "metadata": self._metadata,
            "token_count": self._token_count,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Context":
        """从字典反序列化"""
        context = cls(context_id=data["context_id"])
        context._metadata = data.get("metadata", {})
        context._token_count = data.get("token_count", 0)
        
        # 恢复消息
        for msg_data in data.get("messages", []):
            message = Message(
                role=MessageRole(msg_data["role"]),
                parts=[],
                message_id=msg_data.get("message_id", str(uuid.uuid4())),
                context_id=context.context_id,
            )
            # 简化处理
            from core.schema import MessagePart
            message.parts = [MessagePart.text(msg_data.get("content", ""))]
            context._conversation.messages.append(message)
        
        return context


class ContextManager:
    """上下文管理器（多任务）"""
    
    def __init__(self):
        self._contexts: Dict[str, Context] = {}
        self._default_config = ContextConfig()
    
    def create(
        self,
        context_id: Optional[str] = None,
        config: Optional[ContextConfig] = None,
    ) -> Context:
        """创建新上下文"""
        context = Context(context_id, config or self._default_config)
        self._contexts[context.context_id] = context
        return context
    
    def get(self, context_id: str) -> Optional[Context]:
        """获取上下文"""
        return self._contexts.get(context_id)
    
    def get_or_create(
        self,
        context_id: str,
        config: Optional[ContextConfig] = None,
    ) -> Context:
        """获取或创建上下文"""
        if context_id in self._contexts:
            return self._contexts[context_id]
        return self.create(context_id, config)
    
    def delete(self, context_id: str) -> bool:
        """删除上下文"""
        if context_id in self._contexts:
            del self._contexts[context_id]
            return True
        return False
    
    def list_contexts(self) -> List[str]:
        """列出所有上下文 ID"""
        return list(self._contexts.keys())
    
    def clear_all(self) -> None:
        """清空所有上下文"""
        self._contexts.clear()


# 全局上下文管理器
_context_manager: Optional[ContextManager] = None


def get_context_manager() -> ContextManager:
    """获取全局上下文管理器"""
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
    return _context_manager

