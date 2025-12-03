"""
子代理执行容器模块

SubagentInvocation - 将 Agent 封装为可调用工具。
"""

import asyncio
from typing import Optional, Dict, List, Any, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import logging

from core.schema import (
    ToolResult,
    ToolCallRequest,
    EventType,
    AgentActivityEvent,
)
from core.config import Config
from .registry import AgentDefinition, get_agent_registry
from .basellm import StreamEvent, StreamEventType

logger = logging.getLogger(__name__)


@dataclass
class InvocationResult:
    """调用结果"""
    
    success: bool
    content: str
    display: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    
    def to_tool_result(self, call_id: str) -> ToolResult:
        """转换为 ToolResult"""
        if self.success:
            return ToolResult.success_result(
                call_id=call_id,
                content=self.content,
                display=self.display,
                metadata=self.metadata,
            )
        else:
            return ToolResult.error_result(
                call_id=call_id,
                error=self.error or "Unknown error",
                display=self.display,
            )


class SubagentInvocation:
    """
    子代理执行容器
    
    核心职责:
    - 将 AgentDefinition 封装为可调用工具
    - 初始化并运行 AgentExecutor
    - 流式传递子代理活动 (onActivity → THOUGHT_CHUNK)
    - 统一封装返回 ToolResult
    """
    
    def __init__(
        self,
        definition: AgentDefinition,
        config: Config,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        parent_task_id: Optional[str] = None,
    ):
        self.definition = definition
        self.config = config
        self.task = task
        self.context = context or {}
        self.parent_task_id = parent_task_id
        
        self.invocation_id = str(uuid.uuid4())
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        
        # 活动回调
        self._on_activity: Optional[Callable[[str], None]] = None
        self._on_thought: Optional[Callable[[str], None]] = None
    
    def on_activity(self, callback: Callable[[str], None]) -> None:
        """设置活动回调"""
        self._on_activity = callback
    
    def on_thought(self, callback: Callable[[str], None]) -> None:
        """设置思考回调"""
        self._on_thought = callback
    
    async def execute(
        self,
        update_output: Callable[[str], None],
        abort_signal: Optional[asyncio.Event] = None,
    ) -> ToolResult:
        """
        执行子代理
        
        1. 输出 "Subagent starting..."
        2. 创建 AgentExecutor
        3. 绑定 onActivity 回调
        4. 运行子代理
        5. 封装并返回 ToolResult
        """
        self.started_at = datetime.now()
        
        update_output(f"🚀 子代理启动: {self.definition.name}...")
        
        if self._on_activity:
            self._on_activity(f"子代理 {self.definition.name} 开始执行任务: {self.task}")
        
        try:
            # 延迟导入避免循环依赖
            from .executor import AgentExecutor
            
            # 创建子代理执行器
            executor = AgentExecutor(
                agent_def=self.definition,
                config=self.config,
            )
            
            # 绑定活动回调
            def handle_stream_event(event: StreamEvent):
                if event.type == StreamEventType.CONTENT:
                    if self._on_thought:
                        self._on_thought(event.content)
                    update_output(f"🤖💭 {event.content}")
                elif event.type == StreamEventType.THOUGHT:
                    if event.thought:
                        thought_text = event.thought.description or event.thought.subject
                        if thought_text:
                            if self._on_thought:
                                self._on_thought(thought_text)
                            update_output(f"🤖💭 {thought_text}")
            
            executor.on_stream_event(handle_stream_event)
            
            # 运行子代理
            result = await executor.run(
                user_input=self._build_input(),
                abort_signal=abort_signal,
            )
            
            self.completed_at = datetime.now()
            
            # 封装结果
            return ToolResult(
                call_id=self.invocation_id,
                success=True,
                llm_content=[{
                    "type": "text",
                    "text": f"子代理 {self.definition.name} 执行完成。\n{result.content}",
                }],
                display_content=f"✅ {self.definition.name} 完成: {result.content[:100]}...",
                metadata={
                    "agent_name": self.definition.name,
                    "duration_ms": self._get_duration_ms(),
                    "task": self.task,
                },
            )
            
        except asyncio.CancelledError:
            self.completed_at = datetime.now()
            update_output(f"⚠️ 子代理 {self.definition.name} 被取消")
            
            return ToolResult.error_result(
                call_id=self.invocation_id,
                error="子代理执行被取消",
                display=f"⚠️ {self.definition.name} 已取消",
            )
            
        except Exception as e:
            self.completed_at = datetime.now()
            logger.error(f"[SubagentInvocation] 执行失败: {e}")
            update_output(f"❌ 子代理 {self.definition.name} 执行失败: {e}")
            
            return ToolResult.error_result(
                call_id=self.invocation_id,
                error=str(e),
                display=f"❌ {self.definition.name} 失败: {e}",
            )
    
    def _build_input(self) -> str:
        """构建子代理输入"""
        parts = [f"任务: {self.task}"]
        
        if self.context:
            parts.append(f"\n上下文信息:\n{self._format_context()}")
        
        return "\n".join(parts)
    
    def _format_context(self) -> str:
        """格式化上下文"""
        lines = []
        for key, value in self.context.items():
            if isinstance(value, dict):
                lines.append(f"- {key}:")
                for k, v in value.items():
                    lines.append(f"  - {k}: {v}")
            elif isinstance(value, list):
                lines.append(f"- {key}: {', '.join(str(v) for v in value)}")
            else:
                lines.append(f"- {key}: {value}")
        return "\n".join(lines)
    
    def _get_duration_ms(self) -> Optional[float]:
        """获取执行时长（毫秒）"""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds() * 1000
        return None


class SubagentInvocationBuilder:
    """子代理调用构建器"""
    
    def __init__(self, config: Config):
        self.config = config
        self._registry = get_agent_registry()
    
    def build(
        self,
        agent_name: str,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        parent_task_id: Optional[str] = None,
    ) -> Optional[SubagentInvocation]:
        """构建子代理调用"""
        definition = self._registry.get(agent_name)
        
        if not definition:
            logger.warning(f"[SubagentBuilder] 未找到代理: {agent_name}")
            return None
        
        return SubagentInvocation(
            definition=definition,
            config=self.config,
            task=task,
            context=context,
            parent_task_id=parent_task_id,
        )
    
    def build_from_tool_call(
        self,
        request: ToolCallRequest,
        parent_task_id: Optional[str] = None,
    ) -> Optional[SubagentInvocation]:
        """从工具调用构建"""
        # 检查是否是子代理调用
        agent_name = request.name
        if agent_name.endswith("_agent"):
            task = request.args.get("task", "")
            context = request.args.get("context", {})
            
            invocation = self.build(
                agent_name=agent_name,
                task=task,
                context=context,
                parent_task_id=parent_task_id,
            )
            
            if invocation:
                invocation.invocation_id = request.call_id
            
            return invocation
        
        return None
    
    def is_subagent_call(self, tool_name: str) -> bool:
        """检查是否是子代理调用"""
        return self._registry.get(tool_name) is not None

