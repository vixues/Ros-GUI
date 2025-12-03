"""
Tools 模块

提供 UAV Commander 的工具层实现。
"""

from .tools import (
    DeclarativeTool,
    ToolMethod,
    ToolCategory,
    ToolInvocation,
    CompositeResult,
)

from .tool_registry import (
    ToolRegistry,
    ToolRegistration,
    get_tool_registry,
    register_tool,
    get_tool,
)

from .device_tool import (
    DeviceTool,
    UAVState,
)

from .swarm_tool import (
    SwarmTool,
    FormationType,
    FormationSlot,
    SwarmState,
)


__all__ = [
    # tools
    "DeclarativeTool",
    "ToolMethod",
    "ToolCategory",
    "ToolInvocation",
    "CompositeResult",
    # tool_registry
    "ToolRegistry",
    "ToolRegistration",
    "get_tool_registry",
    "register_tool",
    "get_tool",
    # device_tool
    "DeviceTool",
    "UAVState",
    # swarm_tool
    "SwarmTool",
    "FormationType",
    "FormationSlot",
    "SwarmState",
]


def setup_default_tools() -> None:
    """设置默认工具"""
    registry = get_tool_registry()
    
    # 注册设备工具
    registry.register(DeviceTool())
    
    # 注册集群工具
    registry.register(SwarmTool())

