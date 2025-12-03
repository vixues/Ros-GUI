"""
交互式 REPL 模块

提供命令行交互界面。
"""

import asyncio
import sys
from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass
from enum import Enum
import logging

from core.config import Config, ApprovalMode
from core.agent import (
    AgentExecutor,
    AgentExecutorFactory,
    StreamEvent,
    StreamEventType,
)
from core.schema import ToolConfirmationOutcome

from .commands import CommandHandler, CommandResult

logger = logging.getLogger(__name__)


class REPLState(Enum):
    """REPL 状态"""
    
    IDLE = "idle"
    RUNNING = "running"
    WAITING_CONFIRMATION = "waiting_confirmation"
    EXITING = "exiting"


@dataclass
class REPLConfig:
    """REPL 配置"""
    
    prompt: str = ">>> "
    continuation_prompt: str = "... "
    welcome_message: str = "输入命令控制无人机，输入 'help' 获取帮助，输入 'exit' 退出。"
    stream_enabled: bool = True
    history_file: Optional[str] = None


class REPL:
    """
    交互式 REPL
    
    提供命令行交互界面，支持:
    - 自然语言命令
    - 内置命令（help, exit, status 等）
    - 流式输出
    - 工具确认
    """
    
    def __init__(
        self,
        config: Config,
        repl_config: Optional[REPLConfig] = None,
        stream_enabled: bool = True,
    ):
        self.config = config
        self.repl_config = repl_config or REPLConfig(stream_enabled=stream_enabled)
        
        self.state = REPLState.IDLE
        self._executor: Optional[AgentExecutor] = None
        self._command_handler = CommandHandler(self)
        self._abort_signal = asyncio.Event()
        
        # 待确认的工具调用
        self._pending_confirmations: Dict[str, Dict[str, Any]] = {}
    
    async def run(self) -> None:
        """运行 REPL 主循环"""
        print(self.repl_config.welcome_message)
        print()
        
        # 创建执行器
        factory = AgentExecutorFactory(self.config)
        self._executor = factory.create_coordinator()
        
        if not self._executor:
            print("❌ 无法创建执行器")
            return
        
        # 注册回调
        self._setup_callbacks()
        
        while self.state != REPLState.EXITING:
            try:
                # 获取输入
                user_input = await self._get_input()
                
                if user_input is None:
                    continue
                
                # 处理输入
                await self._process_input(user_input)
                
            except KeyboardInterrupt:
                if self.state == REPLState.RUNNING:
                    print("\n⚠️ 中断执行...")
                    self._abort_signal.set()
                    self.state = REPLState.IDLE
                else:
                    print("\n使用 'exit' 退出")
            
            except EOFError:
                self.state = REPLState.EXITING
            
            except Exception as e:
                logger.error(f"[REPL] 错误: {e}")
                print(f"❌ 错误: {e}")
    
    def _setup_callbacks(self) -> None:
        """设置回调"""
        if not self._executor:
            return
        
        def on_stream(event: StreamEvent):
            if event.type == StreamEventType.CONTENT:
                print(event.content, end="", flush=True)
            elif event.type == StreamEventType.THOUGHT:
                if event.thought and event.thought.description:
                    print(f"\n💭 {event.thought.description}")
        
        def on_output(msg: str):
            print(msg)
        
        if self.repl_config.stream_enabled:
            self._executor.on_stream_event(on_stream)
        self._executor.on_output(on_output)
    
    async def _get_input(self) -> Optional[str]:
        """获取用户输入"""
        prompt = self.repl_config.prompt
        
        if self.state == REPLState.WAITING_CONFIRMATION:
            prompt = "[确认] (y/n/a) >>> "
        
        try:
            # 异步读取输入
            loop = asyncio.get_event_loop()
            user_input = await loop.run_in_executor(
                None,
                lambda: input(prompt)
            )
            return user_input.strip()
        except EOFError:
            return None
    
    async def _process_input(self, user_input: str) -> None:
        """处理用户输入"""
        if not user_input:
            return
        
        # 处理确认状态
        if self.state == REPLState.WAITING_CONFIRMATION:
            await self._handle_confirmation_input(user_input)
            return
        
        # 检查内置命令
        if user_input.startswith("/") or user_input in ["help", "exit", "quit", "status"]:
            result = await self._command_handler.handle(user_input)
            if result.output:
                print(result.output)
            return
        
        # 执行 Agent 命令
        await self._execute_agent_command(user_input)
    
    async def _execute_agent_command(self, command: str) -> None:
        """执行 Agent 命令"""
        if not self._executor:
            print("❌ 执行器未初始化")
            return
        
        self.state = REPLState.RUNNING
        self._abort_signal.clear()
        
        print()  # 空行分隔
        
        try:
            result = await self._executor.run(
                user_input=command,
                abort_signal=self._abort_signal,
            )
            
            print()  # 响应后空行
            
            if not result.success:
                print(f"❌ 执行失败: {result.content}")
            
        finally:
            self.state = REPLState.IDLE
    
    async def _handle_confirmation_input(self, user_input: str) -> None:
        """处理确认输入"""
        user_input = user_input.lower()
        
        if user_input in ["y", "yes", "确认", "是"]:
            outcome = ToolConfirmationOutcome.PROCEED_ONCE
        elif user_input in ["n", "no", "取消", "否"]:
            outcome = ToolConfirmationOutcome.CANCEL
        elif user_input in ["a", "always", "总是"]:
            outcome = ToolConfirmationOutcome.PROCEED_ALWAYS
        else:
            print("请输入 y(确认)/n(取消)/a(总是确认)")
            return
        
        # 处理所有待确认项
        for call_id, info in list(self._pending_confirmations.items()):
            if info.get("on_confirm"):
                await info["on_confirm"](outcome, None)
            del self._pending_confirmations[call_id]
        
        self.state = REPLState.IDLE
    
    def request_confirmation(
        self,
        call_id: str,
        tool_name: str,
        args: Dict[str, Any],
        on_confirm: Callable,
    ) -> None:
        """请求用户确认"""
        self._pending_confirmations[call_id] = {
            "tool_name": tool_name,
            "args": args,
            "on_confirm": on_confirm,
        }
        
        print(f"\n⚠️ 操作需要确认:")
        print(f"   工具: {tool_name}")
        print(f"   参数: {args}")
        
        self.state = REPLState.WAITING_CONFIRMATION
    
    def exit(self) -> None:
        """退出 REPL"""
        self.state = REPLState.EXITING
    
    def cancel_execution(self) -> None:
        """取消当前执行"""
        self._abort_signal.set()
        if self._executor:
            self._executor.cancel()


class SimpleREPL:
    """简化版 REPL（无 Agent）"""
    
    def __init__(self):
        self._command_handler = CommandHandler(None)
    
    async def run(self) -> None:
        """运行简化 REPL"""
        print("UAV Commander 简化模式")
        print("输入 'help' 获取帮助，'exit' 退出")
        print()
        
        while True:
            try:
                user_input = input(">>> ").strip()
                
                if not user_input:
                    continue
                
                if user_input in ["exit", "quit"]:
                    break
                
                result = await self._command_handler.handle(user_input)
                if result.output:
                    print(result.output)
                    
            except KeyboardInterrupt:
                print("\n使用 'exit' 退出")
            except EOFError:
                break
        
        print("👋 再见！")

