"""
Agent 执行器模块

AgentExecutor - 驱动 Agent 运行的主循环。
"""

import asyncio
from typing import (
    Optional,
    Dict,
    List,
    Any,
    Callable,
    AsyncGenerator,
)
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import logging

from core.schema import (
    Message,
    ToolCallRequest,
    ToolResult,
    CompletedToolCall,
    ToolCall,
    ToolSchema,
    ThoughtSummary,
)
from core.config import Config, get_config
from .basellm import BaseLLM, StreamEvent, StreamEventType, LLMResponse
from .llm import create_llm
from .context import Context, ContextConfig
from .registry import AgentDefinition, get_agent_registry
from .scheduler import CoreToolScheduler, SchedulerConfig
from .invocation import SubagentInvocationBuilder
from .prompts import get_prompt_manager

logger = logging.getLogger(__name__)


@dataclass
class ExecutorResult:
    """执行结果"""
    
    success: bool
    content: str
    tool_calls_count: int = 0
    turns: int = 0
    duration_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutorConfig:
    """执行器配置"""
    
    max_turns: int = 20
    max_tool_calls_per_turn: int = 10
    stream_enabled: bool = True
    auto_continue: bool = True  # 工具调用后自动继续


class AgentExecutor:
    """
    Agent 执行器
    
    主循环:
    1. 发送消息给 LLM
    2. 处理 LLM 响应 (内容/工具调用/思考)
    3. 如有工具调用，执行并将结果反馈给 LLM
    4. 重复直到任务完成
    """
    
    def __init__(
        self,
        agent_def: AgentDefinition,
        config: Optional[Config] = None,
        executor_config: Optional[ExecutorConfig] = None,
        llm: Optional[BaseLLM] = None,
    ):
        self.agent_def = agent_def
        self.config = config or get_config()
        self.executor_config = executor_config or ExecutorConfig()
        
        # LLM 客户端
        self.llm = llm or create_llm(
            model_name=agent_def.model or self.config.get_model()
        )
        
        # 上下文
        self.context = Context(config=ContextConfig())
        
        # 工具调度器
        self.scheduler: Optional[CoreToolScheduler] = None
        
        # 子代理构建器
        self._subagent_builder = SubagentInvocationBuilder(self.config)
        
        # 回调
        self._stream_callbacks: List[Callable[[StreamEvent], None]] = []
        self._output_callbacks: List[Callable[[str], None]] = []
        
        # 状态
        self._current_turn = 0
        self._total_tool_calls = 0
        self._abort_signal: Optional[asyncio.Event] = None
        self._is_running = False
        
        # 工具结果收集
        self._completed_tools: List[CompletedToolCall] = []
        self._tool_completion_event = asyncio.Event()
        
        # 初始化
        self._setup()
    
    def _setup(self) -> None:
        """初始化设置"""
        # 设置系统提示词
        prompt_manager = get_prompt_manager()
        if self.agent_def.system_prompt:
            self.llm.set_system_prompt(self.agent_def.system_prompt)
        elif self.agent_def.name == "coordinator":
            prompt = prompt_manager.render(
                "coordinator",
                current_status="待获取",
                available_uavs="待获取",
            )
            self.llm.set_system_prompt(prompt)
        
        # 设置工具
        tools = self._build_tools()
        self.llm.set_tools(tools)
        
        # 创建调度器
        self.scheduler = CoreToolScheduler(
            config=self.config,
            output_update_handler=self._handle_output_update,
            on_tool_calls_update=self._handle_tool_calls_update,
            on_all_tool_calls_complete=self._handle_all_tool_calls_complete,
            tool_executor=self._execute_tool,
        )
    
    def _build_tools(self) -> List[ToolSchema]:
        """构建工具列表"""
        tools = []
        
        # 添加子代理作为工具
        registry = get_agent_registry()
        for tool_name in self.agent_def.tools:
            agent = registry.get(tool_name)
            if agent:
                tools.append(agent.to_tool_schema())
        
        # TODO: 添加普通工具
        
        return tools
    
    def on_stream_event(self, callback: Callable[[StreamEvent], None]) -> None:
        """注册流式事件回调"""
        self._stream_callbacks.append(callback)
    
    def on_output(self, callback: Callable[[str], None]) -> None:
        """注册输出回调"""
        self._output_callbacks.append(callback)
    
    async def run(
        self,
        user_input: str,
        abort_signal: Optional[asyncio.Event] = None,
    ) -> ExecutorResult:
        """
        运行主循环
        
        Args:
            user_input: 用户输入
            abort_signal: 中断信号
        
        Returns:
            执行结果
        """
        if self._is_running:
            raise RuntimeError("Executor 正在运行中")
        
        self._is_running = True
        self._abort_signal = abort_signal or asyncio.Event()
        self._current_turn = 0
        self._total_tool_calls = 0
        start_time = datetime.now()
        
        final_content = ""
        
        try:
            # 添加用户消息
            self.context.add_user_message(user_input)
            
            while self._current_turn < self.executor_config.max_turns:
                self._current_turn += 1
                
                # 检查中断
                if self._abort_signal.is_set():
                    logger.info("[Executor] 收到中断信号")
                    break
                
                logger.info(f"[Executor] 第 {self._current_turn} 轮")
                
                # 调用 LLM
                if self.executor_config.stream_enabled:
                    response = await self._run_stream_turn()
                else:
                    response = await self._run_turn()
                
                # 处理响应
                if response.content:
                    final_content = response.content
                    self.context.add_assistant_message(response.content)
                
                # 处理工具调用
                if response.has_tool_calls:
                    await self._handle_tool_calls(response.tool_calls)
                    
                    # 等待工具完成
                    await self._wait_for_tools()
                    
                    # 添加工具结果到历史
                    for completed in self._completed_tools:
                        self.llm.add_tool_result(completed.result)
                    
                    self._completed_tools.clear()
                    
                    # 自动继续
                    if not self.executor_config.auto_continue:
                        break
                else:
                    # 没有工具调用，结束
                    break
            
            duration = (datetime.now() - start_time).total_seconds() * 1000
            
            return ExecutorResult(
                success=True,
                content=final_content,
                tool_calls_count=self._total_tool_calls,
                turns=self._current_turn,
                duration_ms=duration,
            )
            
        except Exception as e:
            logger.error(f"[Executor] 执行失败: {e}")
            duration = (datetime.now() - start_time).total_seconds() * 1000
            
            return ExecutorResult(
                success=False,
                content=str(e),
                tool_calls_count=self._total_tool_calls,
                turns=self._current_turn,
                duration_ms=duration,
            )
        
        finally:
            self._is_running = False
    
    async def _run_turn(self) -> LLMResponse:
        """运行一轮（非流式）"""
        messages = self.context.get_llm_messages()
        tools = [t.to_openai_format() for t in self.llm._tools]
        
        return await self.llm.generate(messages, tools)
    
    async def _run_stream_turn(self) -> LLMResponse:
        """运行一轮（流式）"""
        messages = self.context.get_llm_messages()
        tools = [t.to_openai_format() for t in self.llm._tools]
        
        content_parts = []
        tool_calls = []
        
        async for event in self.llm.generate_stream(
            messages, tools, self._abort_signal
        ):
            # 通知回调
            for callback in self._stream_callbacks:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"[Executor] 流回调失败: {e}")
            
            if event.type == StreamEventType.CONTENT:
                content_parts.append(event.content)
            elif event.type == StreamEventType.TOOL_CALL:
                tool_calls.append(event.tool_call)
            elif event.type == StreamEventType.ERROR:
                raise RuntimeError(event.error)
        
        return LLMResponse(
            content="".join(content_parts),
            tool_calls=tool_calls,
        )
    
    async def _handle_tool_calls(
        self,
        tool_calls: List[ToolCallRequest],
    ) -> None:
        """处理工具调用"""
        if not tool_calls:
            return
        
        self._total_tool_calls += len(tool_calls)
        logger.info(f"[Executor] 处理 {len(tool_calls)} 个工具调用")
        
        # 重置完成事件
        self._tool_completion_event.clear()
        
        # 调度执行
        await self.scheduler.schedule(tool_calls, self._abort_signal)
    
    async def _wait_for_tools(self) -> None:
        """等待工具完成"""
        if self.scheduler.is_idle():
            return
        
        logger.info("[Executor] 等待工具完成...")
        await self._tool_completion_event.wait()
    
    async def _execute_tool(
        self,
        tool_name: str,
        args: Dict[str, Any],
    ) -> ToolResult:
        """执行工具"""
        # 检查是否是子代理调用
        if self._subagent_builder.is_subagent_call(tool_name):
            return await self._execute_subagent(tool_name, args)
        
        # 普通工具调用
        return await self._execute_regular_tool(tool_name, args)
    
    async def _execute_subagent(
        self,
        agent_name: str,
        args: Dict[str, Any],
    ) -> ToolResult:
        """执行子代理"""
        task = args.get("task", "")
        context = args.get("context", {})
        
        invocation = self._subagent_builder.build(
            agent_name=agent_name,
            task=task,
            context=context,
        )
        
        if not invocation:
            return ToolResult.error_result(
                call_id=str(uuid.uuid4()),
                error=f"未找到代理: {agent_name}",
            )
        
        def output_handler(msg: str):
            for callback in self._output_callbacks:
                callback(msg)
        
        return await invocation.execute(
            update_output=output_handler,
            abort_signal=self._abort_signal,
        )
    
    async def _execute_regular_tool(
        self,
        tool_name: str,
        args: Dict[str, Any],
    ) -> ToolResult:
        """执行普通工具"""
        # TODO: 实现工具注册表查找和执行
        # 临时返回模拟结果
        return ToolResult.success_result(
            call_id=str(uuid.uuid4()),
            content=f"工具 {tool_name} 执行完成，参数: {args}",
            display=f"✅ {tool_name} 完成",
        )
    
    def _handle_output_update(
        self,
        call_id: str,
        output: Any,
    ) -> None:
        """处理输出更新"""
        output_str = str(output) if not isinstance(output, str) else output
        
        for callback in self._output_callbacks:
            try:
                callback(output_str)
            except Exception as e:
                logger.error(f"[Executor] 输出回调失败: {e}")
    
    def _handle_tool_calls_update(
        self,
        tool_calls: List[ToolCall],
    ) -> None:
        """处理工具状态更新"""
        for tc in tool_calls:
            logger.debug(
                f"[Executor] 工具 {tc.request.name} 状态: {tc.status.value}"
            )
    
    async def _handle_all_tool_calls_complete(
        self,
        completed_tools: List[CompletedToolCall],
    ) -> None:
        """处理所有工具完成"""
        self._completed_tools.extend(completed_tools)
        self._tool_completion_event.set()
        
        logger.info(
            f"[Executor] 工具调用批次完成: "
            f"{[tc.request.name for tc in completed_tools]}"
        )
    
    def cancel(self) -> None:
        """取消执行"""
        if self._abort_signal:
            self._abort_signal.set()
        
        if self.scheduler:
            self.scheduler.cancel_all("用户取消")


class AgentExecutorFactory:
    """执行器工厂"""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or get_config()
        self._registry = get_agent_registry()
    
    def create(
        self,
        agent_name: str,
        executor_config: Optional[ExecutorConfig] = None,
    ) -> Optional[AgentExecutor]:
        """创建执行器"""
        agent_def = self._registry.get(agent_name)
        
        if not agent_def:
            logger.warning(f"[ExecutorFactory] 未找到代理: {agent_name}")
            return None
        
        return AgentExecutor(
            agent_def=agent_def,
            config=self.config,
            executor_config=executor_config,
        )
    
    def create_coordinator(
        self,
        executor_config: Optional[ExecutorConfig] = None,
    ) -> AgentExecutor:
        """创建协调器执行器"""
        executor = self.create("coordinator", executor_config)
        if not executor:
            raise RuntimeError("无法创建协调器")
        return executor

