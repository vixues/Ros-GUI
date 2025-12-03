"""
LLM 抽象基类模块

定义 LLM 客户端的统一接口规范。
"""

import asyncio
from abc import ABC, abstractmethod
from typing import (
    Optional,
    Dict,
    List,
    Any,
    AsyncGenerator,
    Callable,
    Awaitable,
    Union,
)
from dataclasses import dataclass, field
from enum import Enum
import logging

from core.schema import (
    Message,
    MessageRole,
    ToolCallRequest,
    ToolResult,
    ToolSchema,
    ThoughtSummary,
)
from core.config import LLMSettings, ModelConfig

logger = logging.getLogger(__name__)


class StreamEventType(Enum):
    """流式事件类型"""
    
    CONTENT = "content"           # 文本内容
    TOOL_CALL = "tool_call"       # 工具调用
    THOUGHT = "thought"           # 思考过程
    FINISHED = "finished"         # 完成
    ERROR = "error"               # 错误


@dataclass
class StreamEvent:
    """流式事件"""
    
    type: StreamEventType
    content: Optional[str] = None
    tool_call: Optional[ToolCallRequest] = None
    thought: Optional[ThoughtSummary] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def text(cls, content: str) -> "StreamEvent":
        return cls(type=StreamEventType.CONTENT, content=content)
    
    @classmethod
    def tool(cls, request: ToolCallRequest) -> "StreamEvent":
        return cls(type=StreamEventType.TOOL_CALL, tool_call=request)
    
    @classmethod
    def think(cls, thought: ThoughtSummary) -> "StreamEvent":
        return cls(type=StreamEventType.THOUGHT, thought=thought)
    
    @classmethod
    def finish(cls) -> "StreamEvent":
        return cls(type=StreamEventType.FINISHED)
    
    @classmethod
    def fail(cls, error: str) -> "StreamEvent":
        return cls(type=StreamEventType.ERROR, error=error)


@dataclass
class LLMResponse:
    """LLM 响应"""
    
    content: str = ""
    tool_calls: List[ToolCallRequest] = field(default_factory=list)
    thoughts: List[ThoughtSummary] = field(default_factory=list)
    finish_reason: str = "stop"
    usage: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0


class BaseLLM(ABC):
    """LLM 抽象基类"""
    
    def __init__(
        self,
        settings: Optional[LLMSettings] = None,
        model_config: Optional[ModelConfig] = None,
    ):
        self.settings = settings or LLMSettings()
        self.model_config = model_config or self.settings.get_model_config(
            self.settings.default_model
        )
        self._history: List[Dict[str, Any]] = []
        self._system_prompt: Optional[str] = None
        self._tools: List[ToolSchema] = []
    
    @property
    def model_name(self) -> str:
        return self.model_config.name
    
    def set_system_prompt(self, prompt: str) -> None:
        """设置系统提示词"""
        self._system_prompt = prompt
    
    def set_tools(self, tools: List[ToolSchema]) -> None:
        """设置可用工具"""
        self._tools = tools
    
    def add_message(self, message: Message) -> None:
        """添加消息到历史"""
        self._history.append(self._message_to_dict(message))
    
    def add_tool_result(self, result: ToolResult) -> None:
        """添加工具结果到历史"""
        self._history.append({
            "role": "tool",
            "tool_call_id": result.call_id,
            "content": self._format_tool_result(result),
        })
    
    def clear_history(self) -> None:
        """清空历史"""
        self._history.clear()
    
    def get_history(self) -> List[Dict[str, Any]]:
        """获取历史"""
        return self._history.copy()
    
    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> LLMResponse:
        """
        生成响应
        
        Args:
            messages: 消息列表
            tools: 可用工具
            **kwargs: 额外参数
        
        Returns:
            LLM 响应
        """
        pass
    
    @abstractmethod
    async def generate_stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        abort_signal: Optional[asyncio.Event] = None,
        **kwargs,
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        流式生成响应
        
        Args:
            messages: 消息列表
            tools: 可用工具
            abort_signal: 中断信号
            **kwargs: 额外参数
        
        Yields:
            流式事件
        """
        pass
    
    async def chat(
        self,
        user_message: str,
        stream: bool = True,
        abort_signal: Optional[asyncio.Event] = None,
    ) -> Union[LLMResponse, AsyncGenerator[StreamEvent, None]]:
        """
        对话接口
        
        Args:
            user_message: 用户消息
            stream: 是否流式
            abort_signal: 中断信号
        
        Returns:
            响应或流式事件生成器
        """
        # 构建消息列表
        messages = self._build_messages(user_message)
        
        # 构建工具列表
        tools = [t.to_openai_format() for t in self._tools] if self._tools else None
        
        if stream:
            return self.generate_stream(messages, tools, abort_signal)
        else:
            return await self.generate(messages, tools)
    
    def _build_messages(self, user_message: str) -> List[Dict[str, Any]]:
        """构建消息列表"""
        messages = []
        
        # 添加系统提示
        if self._system_prompt:
            messages.append({
                "role": "system",
                "content": self._system_prompt,
            })
        
        # 添加历史消息
        messages.extend(self._history)
        
        # 添加用户消息
        messages.append({
            "role": "user",
            "content": user_message,
        })
        
        return messages
    
    def _message_to_dict(self, message: Message) -> Dict[str, Any]:
        """将 Message 转换为字典"""
        return {
            "role": message.role.value,
            "content": message.text_content,
        }
    
    def _format_tool_result(self, result: ToolResult) -> str:
        """格式化工具结果"""
        if result.llm_content:
            parts = []
            for item in result.llm_content:
                if isinstance(item, dict) and "text" in item:
                    parts.append(item["text"])
                elif isinstance(item, str):
                    parts.append(item)
            return "\n".join(parts)
        return result.display_content or ""


class LLMWithFallback(BaseLLM):
    """带故障转移的 LLM"""
    
    def __init__(
        self,
        primary: BaseLLM,
        fallback: Optional[BaseLLM] = None,
        fallback_handler: Optional[Callable[[], Awaitable[str]]] = None,
    ):
        super().__init__(primary.settings, primary.model_config)
        self.primary = primary
        self.fallback = fallback
        self.fallback_handler = fallback_handler
        self._use_fallback = False
    
    async def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> LLMResponse:
        try:
            return await self.primary.generate(messages, tools, **kwargs)
        except Exception as e:
            logger.warning(f"主 LLM 失败: {e}, 尝试回退")
            return await self._handle_fallback(messages, tools, **kwargs)
    
    async def generate_stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        abort_signal: Optional[asyncio.Event] = None,
        **kwargs,
    ) -> AsyncGenerator[StreamEvent, None]:
        try:
            async for event in self.primary.generate_stream(
                messages, tools, abort_signal, **kwargs
            ):
                yield event
        except Exception as e:
            logger.warning(f"主 LLM 流失败: {e}, 尝试回退")
            async for event in self._handle_fallback_stream(
                messages, tools, abort_signal, **kwargs
            ):
                yield event
    
    async def _handle_fallback(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]],
        **kwargs,
    ) -> LLMResponse:
        if self.fallback_handler:
            action = await self.fallback_handler()
            if action == "stop":
                return LLMResponse(
                    content="请求已停止",
                    finish_reason="stop",
                )
        
        if self.fallback:
            self._use_fallback = True
            return await self.fallback.generate(messages, tools, **kwargs)
        
        raise RuntimeError("LLM 请求失败且无可用回退")
    
    async def _handle_fallback_stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]],
        abort_signal: Optional[asyncio.Event],
        **kwargs,
    ) -> AsyncGenerator[StreamEvent, None]:
        if self.fallback_handler:
            action = await self.fallback_handler()
            if action == "stop":
                yield StreamEvent.text("请求已停止")
                yield StreamEvent.finish()
                return
        
        if self.fallback:
            self._use_fallback = True
            async for event in self.fallback.generate_stream(
                messages, tools, abort_signal, **kwargs
            ):
                yield event
        else:
            yield StreamEvent.fail("LLM 请求失败且无可用回退")

