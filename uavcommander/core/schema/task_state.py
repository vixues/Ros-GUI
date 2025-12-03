"""
任务状态定义模块

定义任务在整个生命周期中的状态流转。
"""

from enum import Enum
from typing import Optional
from dataclasses import dataclass
from datetime import datetime


class TaskState(Enum):
    """任务状态枚举"""
    
    SUBMITTED = "submitted"        # 任务已提交，等待处理
    WORKING = "working"            # 任务正在执行中
    INPUT_REQUIRED = "input-required"  # 需要用户输入/确认
    COMPLETED = "completed"        # 任务成功完成
    FAILED = "failed"              # 任务执行失败
    CANCELLED = "cancelled"        # 任务被取消


class ToolCallStatus(Enum):
    """工具调用状态"""
    
    SCHEDULED = "scheduled"        # 已调度，等待执行
    EXECUTING = "executing"        # 正在执行
    AWAITING_APPROVAL = "awaiting_approval"  # 等待用户确认
    SUCCESS = "success"            # 执行成功
    ERROR = "error"                # 执行失败
    CANCELLED = "cancelled"        # 被取消


@dataclass
class TaskStateTransition:
    """任务状态转换记录"""
    
    from_state: TaskState
    to_state: TaskState
    timestamp: datetime
    reason: Optional[str] = None
    
    def __post_init__(self):
        if not isinstance(self.timestamp, datetime):
            self.timestamp = datetime.now()


# 定义有效的状态转换
VALID_TRANSITIONS = {
    TaskState.SUBMITTED: [TaskState.WORKING, TaskState.CANCELLED],
    TaskState.WORKING: [
        TaskState.WORKING,  # 工具调用后继续工作
        TaskState.INPUT_REQUIRED,
        TaskState.COMPLETED,
        TaskState.FAILED,
        TaskState.CANCELLED,
    ],
    TaskState.INPUT_REQUIRED: [
        TaskState.WORKING,  # 用户确认后继续
        TaskState.CANCELLED,
        TaskState.FAILED,
    ],
    TaskState.COMPLETED: [],  # 终态
    TaskState.FAILED: [],     # 终态
    TaskState.CANCELLED: [],  # 终态
}


def is_valid_transition(from_state: TaskState, to_state: TaskState) -> bool:
    """检查状态转换是否有效"""
    return to_state in VALID_TRANSITIONS.get(from_state, [])


def is_terminal_state(state: TaskState) -> bool:
    """检查是否是终态"""
    return state in [TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED]

