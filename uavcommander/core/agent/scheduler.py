"""
工具调度器模块

CoreToolScheduler - 管理工具调用的完整生命周期。
"""

import asyncio
from typing import (
    Optional,
    Dict,
    List,
    Any,
    Callable,
    Awaitable,
    Union,
)
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

from core.schema import (
    ToolCallRequest,
    ToolResult,
    ToolCall,
    ToolCallStatus,
    ToolConfirmationDetails,
    ToolConfirmationOutcome,
    CompletedToolCall,
    ToolType,
)
from core.config import Config, ApprovalMode, get_safety_policy, SafetyAction

logger = logging.getLogger(__name__)


# 输出类型
AnsiOutput = List[List[Dict[str, str]]]
OutputType = Union[str, AnsiOutput]

# 回调类型
OutputUpdateHandler = Callable[[str, OutputType], None]
ToolCallsUpdateHandler = Callable[[List[ToolCall]], None]
AllToolCallsCompleteHandler = Callable[[List[CompletedToolCall]], Awaitable[None]]


@dataclass
class SchedulerConfig:
    """调度器配置"""
    
    max_concurrent: int = 5
    default_timeout: float = 60.0
    retry_count: int = 0
    confirm_dangerous: bool = True


class CoreToolScheduler:
    """
    核心工具调度器
    
    职责:
    - 调度工具执行
    - 管理工具生命周期 (Scheduled → Executing → Success/Error)
    - 控制是否需要确认执行
    - 执行前后钩子
    - 组织执行结果并返回
    """
    
    def __init__(
        self,
        config: Config,
        output_update_handler: OutputUpdateHandler,
        on_tool_calls_update: ToolCallsUpdateHandler,
        on_all_tool_calls_complete: AllToolCallsCompleteHandler,
        tool_executor: Optional[Callable[[str, Dict[str, Any]], Awaitable[ToolResult]]] = None,
        scheduler_config: Optional[SchedulerConfig] = None,
    ):
        self.config = config
        self.scheduler_config = scheduler_config or SchedulerConfig()
        
        # 回调
        self._output_update = output_update_handler
        self._on_tool_calls_update = on_tool_calls_update
        self._on_all_tool_calls_complete = on_all_tool_calls_complete
        
        # 工具执行器
        self._tool_executor = tool_executor
        
        # 状态
        self._pending_calls: Dict[str, ToolCall] = {}
        self._executing_count = 0
        self._semaphore = asyncio.Semaphore(self.scheduler_config.max_concurrent)
        
        # 确认相关
        self._always_approved_tools: set = set()
        self._always_approved_servers: set = set()
    
    async def schedule(
        self,
        requests: List[ToolCallRequest],
        abort_signal: asyncio.Event,
    ) -> None:
        """
        调度一批工具调用
        
        1. 为每个请求创建 ToolCall
        2. 检查是否需要确认
        3. 执行工具
        4. 收集结果
        """
        if not requests:
            return
        
        logger.info(f"[Scheduler] 调度 {len(requests)} 个工具调用")
        
        # 创建 ToolCall 对象
        tool_calls = []
        for request in requests:
            tool_call = ToolCall(
                request=request,
                status=ToolCallStatus.SCHEDULED,
            )
            self._pending_calls[request.call_id] = tool_call
            tool_calls.append(tool_call)
        
        # 通知状态更新
        self._on_tool_calls_update(tool_calls)
        
        # 并发执行
        tasks = []
        for tool_call in tool_calls:
            task = asyncio.create_task(
                self._execute_tool_call(tool_call, abort_signal)
            )
            tasks.append(task)
        
        # 等待所有任务完成
        completed_calls = []
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for tool_call, result in zip(tool_calls, results):
            if isinstance(result, Exception):
                logger.error(f"[Scheduler] 工具 {tool_call.request.name} 执行异常: {result}")
                tool_call.status = ToolCallStatus.ERROR
                tool_call.result = ToolResult.error_result(
                    tool_call.request.call_id,
                    str(result)
                )
            
            if tool_call.result:
                completed_calls.append(CompletedToolCall(
                    request=tool_call.request,
                    result=tool_call.result,
                ))
            
            # 清理
            if tool_call.request.call_id in self._pending_calls:
                del self._pending_calls[tool_call.request.call_id]
        
        # 通知完成
        if completed_calls:
            await self._on_all_tool_calls_complete(completed_calls)
    
    async def _execute_tool_call(
        self,
        tool_call: ToolCall,
        abort_signal: asyncio.Event,
    ) -> None:
        """执行单个工具调用"""
        request = tool_call.request
        
        # 检查中断
        if abort_signal.is_set():
            tool_call.status = ToolCallStatus.CANCELLED
            self._on_tool_calls_update([tool_call])
            return
        
        # 检查是否需要确认
        if self._should_confirm(request.name, request.args):
            await self._handle_confirmation(tool_call, abort_signal)
            
            # 确认后检查状态
            if tool_call.status == ToolCallStatus.CANCELLED:
                return
        
        # 执行工具
        await self._execute_with_hooks(tool_call, abort_signal)
    
    def _should_confirm(self, tool_name: str, args: Dict[str, Any]) -> bool:
        """判断是否需要确认"""
        # YOLO 模式不需要确认
        if self.config.get_approval_mode() == ApprovalMode.YOLO:
            return False
        
        # 检查是否已标记为总是允许
        if tool_name in self._always_approved_tools:
            return False
        
        # 检查安全策略
        policy = get_safety_policy()
        action, _ = policy.validate_operation(tool_name, args)
        
        if action == SafetyAction.CONFIRM:
            return True
        
        # STRICT 模式所有操作都需要确认
        if self.config.get_approval_mode() == ApprovalMode.STRICT:
            return True
        
        return False
    
    async def _handle_confirmation(
        self,
        tool_call: ToolCall,
        abort_signal: asyncio.Event,
    ) -> None:
        """处理确认流程"""
        request = tool_call.request
        
        # 创建确认事件
        confirmation_event = asyncio.Event()
        confirmation_outcome: Optional[ToolConfirmationOutcome] = None
        modified_args: Optional[Dict[str, Any]] = None
        
        async def on_confirm(
            outcome: ToolConfirmationOutcome,
            payload: Optional[Dict[str, Any]] = None,
        ) -> None:
            nonlocal confirmation_outcome, modified_args
            confirmation_outcome = outcome
            modified_args = payload
            confirmation_event.set()
        
        # 设置确认详情
        policy = get_safety_policy()
        risk_level = policy.get_risk_level(request.name)
        
        tool_call.confirmation_details = ToolConfirmationDetails(
            type=risk_level.value,
            tool_name=request.name,
            args=request.args,
            description=f"工具 {request.name} 需要确认执行",
            on_confirm=on_confirm,
        )
        tool_call.status = ToolCallStatus.AWAITING_APPROVAL
        
        # 通知等待确认
        self._on_tool_calls_update([tool_call])
        self._output_update(
            request.call_id,
            f"⚠️ 工具 {request.name} 需要确认执行，参数: {request.args}"
        )
        
        # 等待确认
        try:
            await asyncio.wait_for(
                confirmation_event.wait(),
                timeout=300.0  # 5分钟超时
            )
        except asyncio.TimeoutError:
            tool_call.status = ToolCallStatus.CANCELLED
            tool_call.result = ToolResult.error_result(
                request.call_id,
                "确认超时，操作已取消"
            )
            self._on_tool_calls_update([tool_call])
            return
        
        # 处理确认结果
        if confirmation_outcome == ToolConfirmationOutcome.CANCEL:
            tool_call.status = ToolCallStatus.CANCELLED
            tool_call.result = ToolResult.error_result(
                request.call_id,
                "用户取消了操作"
            )
            self._on_tool_calls_update([tool_call])
            return
        
        if confirmation_outcome == ToolConfirmationOutcome.PROCEED_ALWAYS:
            self._always_approved_tools.add(request.name)
        
        if confirmation_outcome == ToolConfirmationOutcome.MODIFY and modified_args:
            request.args = modified_args
        
        # 清除确认详情，继续执行
        tool_call.confirmation_details = None
    
    async def _execute_with_hooks(
        self,
        tool_call: ToolCall,
        abort_signal: asyncio.Event,
    ) -> None:
        """带钩子的工具执行"""
        request = tool_call.request
        
        # 获取信号量
        async with self._semaphore:
            # 再次检查中断
            if abort_signal.is_set():
                tool_call.status = ToolCallStatus.CANCELLED
                return
            
            # 更新状态为执行中
            tool_call.status = ToolCallStatus.EXECUTING
            tool_call.started_at = datetime.now()
            self._on_tool_calls_update([tool_call])
            
            self._output_update(
                request.call_id,
                f"🔧 执行工具: {request.name}"
            )
            
            try:
                # 执行工具
                if self._tool_executor:
                    result = await asyncio.wait_for(
                        self._tool_executor(request.name, request.args),
                        timeout=self.scheduler_config.default_timeout
                    )
                else:
                    # 默认模拟执行
                    result = await self._default_execute(request)
                
                tool_call.result = result
                tool_call.status = ToolCallStatus.SUCCESS
                tool_call.completed_at = datetime.now()
                
                self._output_update(
                    request.call_id,
                    result.display_content or f"✅ {request.name} 执行成功"
                )
                
            except asyncio.TimeoutError:
                tool_call.status = ToolCallStatus.ERROR
                tool_call.result = ToolResult.error_result(
                    request.call_id,
                    f"工具执行超时 ({self.scheduler_config.default_timeout}s)"
                )
                tool_call.completed_at = datetime.now()
                
            except Exception as e:
                logger.error(f"[Scheduler] 工具执行失败: {e}")
                tool_call.status = ToolCallStatus.ERROR
                tool_call.result = ToolResult.error_result(
                    request.call_id,
                    str(e)
                )
                tool_call.completed_at = datetime.now()
            
            # 通知更新
            self._on_tool_calls_update([tool_call])
    
    async def _default_execute(self, request: ToolCallRequest) -> ToolResult:
        """默认执行（模拟）"""
        # 模拟执行延迟
        await asyncio.sleep(0.1)
        
        return ToolResult.success_result(
            call_id=request.call_id,
            content=f"工具 {request.name} 执行完成，参数: {request.args}",
            display=f"✅ {request.name} 完成",
        )
    
    def cancel_all(self, reason: str) -> None:
        """取消所有待处理的工具调用"""
        for call_id, tool_call in list(self._pending_calls.items()):
            if tool_call.status in [ToolCallStatus.SCHEDULED, ToolCallStatus.AWAITING_APPROVAL]:
                tool_call.status = ToolCallStatus.CANCELLED
                tool_call.result = ToolResult.error_result(call_id, reason)
        
        logger.info(f"[Scheduler] 取消所有工具调用: {reason}")
    
    def get_pending_count(self) -> int:
        """获取待处理数量"""
        return len(self._pending_calls)
    
    def is_idle(self) -> bool:
        """是否空闲"""
        return len(self._pending_calls) == 0
