"""
自动执行器模块

Automator - 多轮对话自动驱动和任务完成判断。
"""

import asyncio
from typing import Optional, Dict, List, Any, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

from core.config import Config, get_config
from .executor import AgentExecutor, AgentExecutorFactory, ExecutorConfig, ExecutorResult
from .registry import AgentDefinition

logger = logging.getLogger(__name__)


class AutomatorState(Enum):
    """自动执行器状态"""
    
    IDLE = "idle"
    RUNNING = "running"
    WAITING_INPUT = "waiting_input"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AutomatorConfig:
    """自动执行器配置"""
    
    # 最大自动轮次
    max_auto_turns: int = 10
    
    # 单轮超时（秒）
    turn_timeout: float = 120.0
    
    # 总超时（秒）
    total_timeout: float = 600.0
    
    # 是否需要用户确认继续
    require_confirmation: bool = False
    
    # 完成判断回调
    completion_checker: Optional[Callable[[str], bool]] = None


@dataclass
class AutomatorResult:
    """自动执行结果"""
    
    success: bool
    final_response: str
    turns: int
    total_tool_calls: int
    duration_ms: float
    history: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None


class Automator:
    """
    自动执行器
    
    职责:
    - 多轮对话自动驱动
    - 任务完成判断
    - 超时控制
    - 中断处理
    """
    
    def __init__(
        self,
        executor: AgentExecutor,
        config: Optional[AutomatorConfig] = None,
    ):
        self.executor = executor
        self.config = config or AutomatorConfig()
        
        self.state = AutomatorState.IDLE
        self._current_turn = 0
        self._total_tool_calls = 0
        self._history: List[Dict[str, Any]] = []
        
        self._abort_signal = asyncio.Event()
        self._continue_signal = asyncio.Event()
        
        # 回调
        self._on_turn_complete: Optional[Callable[[int, str], Awaitable[None]]] = None
        self._on_state_change: Optional[Callable[[AutomatorState], None]] = None
    
    def on_turn_complete(
        self,
        callback: Callable[[int, str], Awaitable[None]],
    ) -> None:
        """设置轮次完成回调"""
        self._on_turn_complete = callback
    
    def on_state_change(
        self,
        callback: Callable[[AutomatorState], None],
    ) -> None:
        """设置状态变更回调"""
        self._on_state_change = callback
    
    def _set_state(self, state: AutomatorState) -> None:
        """设置状态"""
        self.state = state
        if self._on_state_change:
            self._on_state_change(state)
    
    async def run(
        self,
        initial_input: str,
    ) -> AutomatorResult:
        """
        运行自动执行
        
        Args:
            initial_input: 初始输入
        
        Returns:
            执行结果
        """
        if self.state == AutomatorState.RUNNING:
            raise RuntimeError("Automator 正在运行中")
        
        self._set_state(AutomatorState.RUNNING)
        self._current_turn = 0
        self._total_tool_calls = 0
        self._history.clear()
        start_time = datetime.now()
        
        current_input = initial_input
        final_response = ""
        
        try:
            # 设置总超时
            async with asyncio.timeout(self.config.total_timeout):
                while self._current_turn < self.config.max_auto_turns:
                    # 检查中断
                    if self._abort_signal.is_set():
                        self._set_state(AutomatorState.CANCELLED)
                        break
                    
                    self._current_turn += 1
                    logger.info(f"[Automator] 自动轮次 {self._current_turn}")
                    
                    # 执行一轮
                    try:
                        async with asyncio.timeout(self.config.turn_timeout):
                            result = await self.executor.run(
                                user_input=current_input,
                                abort_signal=self._abort_signal,
                            )
                    except asyncio.TimeoutError:
                        logger.warning(f"[Automator] 轮次 {self._current_turn} 超时")
                        continue
                    
                    # 记录历史
                    self._history.append({
                        "turn": self._current_turn,
                        "input": current_input,
                        "output": result.content,
                        "tool_calls": result.tool_calls_count,
                    })
                    
                    self._total_tool_calls += result.tool_calls_count
                    final_response = result.content
                    
                    # 触发回调
                    if self._on_turn_complete:
                        await self._on_turn_complete(self._current_turn, result.content)
                    
                    # 检查是否完成
                    if self._is_completed(result):
                        self._set_state(AutomatorState.COMPLETED)
                        break
                    
                    # 检查是否需要用户输入
                    if self._needs_user_input(result):
                        self._set_state(AutomatorState.WAITING_INPUT)
                        
                        # 等待用户输入
                        user_input = await self._wait_for_input()
                        if user_input is None:
                            break
                        
                        current_input = user_input
                        self._set_state(AutomatorState.RUNNING)
                    else:
                        # 继续下一轮
                        if self.config.require_confirmation:
                            if not await self._wait_for_confirmation():
                                break
                        
                        # 使用空输入继续
                        current_input = "继续"
            
            duration = (datetime.now() - start_time).total_seconds() * 1000
            
            if self.state == AutomatorState.RUNNING:
                self._set_state(AutomatorState.COMPLETED)
            
            return AutomatorResult(
                success=self.state == AutomatorState.COMPLETED,
                final_response=final_response,
                turns=self._current_turn,
                total_tool_calls=self._total_tool_calls,
                duration_ms=duration,
                history=self._history,
            )
            
        except asyncio.TimeoutError:
            self._set_state(AutomatorState.FAILED)
            duration = (datetime.now() - start_time).total_seconds() * 1000
            
            return AutomatorResult(
                success=False,
                final_response=final_response,
                turns=self._current_turn,
                total_tool_calls=self._total_tool_calls,
                duration_ms=duration,
                history=self._history,
                error="执行超时",
            )
            
        except Exception as e:
            self._set_state(AutomatorState.FAILED)
            duration = (datetime.now() - start_time).total_seconds() * 1000
            
            return AutomatorResult(
                success=False,
                final_response=final_response,
                turns=self._current_turn,
                total_tool_calls=self._total_tool_calls,
                duration_ms=duration,
                history=self._history,
                error=str(e),
            )
    
    def _is_completed(self, result: ExecutorResult) -> bool:
        """判断是否完成"""
        # 如果没有工具调用，可能是完成了
        if result.tool_calls_count == 0:
            return True
        
        # 使用自定义检查器
        if self.config.completion_checker:
            return self.config.completion_checker(result.content)
        
        # 检查响应中的完成标志
        completion_phrases = [
            "任务完成",
            "已完成",
            "执行成功",
            "操作成功",
            "已经完成",
        ]
        
        for phrase in completion_phrases:
            if phrase in result.content:
                return True
        
        return False
    
    def _needs_user_input(self, result: ExecutorResult) -> bool:
        """判断是否需要用户输入"""
        # 检查响应中的询问标志
        question_phrases = [
            "请问",
            "您需要",
            "是否",
            "请选择",
            "请确认",
            "？",
        ]
        
        for phrase in question_phrases:
            if phrase in result.content:
                return True
        
        return False
    
    async def _wait_for_input(self) -> Optional[str]:
        """等待用户输入"""
        self._continue_signal.clear()
        
        # 等待输入或取消
        done, pending = await asyncio.wait(
            [
                asyncio.create_task(self._continue_signal.wait()),
                asyncio.create_task(self._abort_signal.wait()),
            ],
            return_when=asyncio.FIRST_COMPLETED,
        )
        
        for task in pending:
            task.cancel()
        
        if self._abort_signal.is_set():
            return None
        
        return getattr(self, "_pending_input", None)
    
    async def _wait_for_confirmation(self) -> bool:
        """等待确认继续"""
        return await self._wait_for_input() is not None
    
    def provide_input(self, user_input: str) -> None:
        """提供用户输入"""
        self._pending_input = user_input
        self._continue_signal.set()
    
    def cancel(self) -> None:
        """取消执行"""
        self._abort_signal.set()
        self.executor.cancel()


class AutomatorFactory:
    """自动执行器工厂"""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or get_config()
        self._executor_factory = AgentExecutorFactory(self.config)
    
    def create(
        self,
        agent_name: str = "coordinator",
        automator_config: Optional[AutomatorConfig] = None,
        executor_config: Optional[ExecutorConfig] = None,
    ) -> Optional[Automator]:
        """创建自动执行器"""
        executor = self._executor_factory.create(agent_name, executor_config)
        
        if not executor:
            return None
        
        return Automator(executor, automator_config)
    
    def create_default(
        self,
        automator_config: Optional[AutomatorConfig] = None,
    ) -> Automator:
        """创建默认自动执行器"""
        automator = self.create("coordinator", automator_config)
        if not automator:
            raise RuntimeError("无法创建自动执行器")
        return automator

