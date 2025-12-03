# Schema 模块

> 📋 数据模式定义层

本模块定义了 UAV Commander 系统中使用的所有数据结构和类型。

## 📁 模块结构

```
schema/
├── __init__.py          # 模块导出
├── task_state.py        # 任务状态定义
├── messages.py          # 消息类型定义
├── events.py            # 事件类型定义
├── tool_call.py         # 工具调用类型
└── README.md            # 本文档
```

## 🔧 核心类型

### 任务状态 (task_state.py)

```python
class TaskState(Enum):
    SUBMITTED = "submitted"        # 已提交
    WORKING = "working"            # 执行中
    INPUT_REQUIRED = "input-required"  # 需要输入
    COMPLETED = "completed"        # 已完成
    FAILED = "failed"              # 失败
    CANCELLED = "cancelled"        # 已取消
```

### 消息类型 (messages.py)

- `Message` - 基础消息
- `MessagePart` - 消息片段
- `ConversationContext` - 对话上下文

### 事件类型 (events.py)

- `TaskEvent` - 任务事件
- `ToolCallEvent` - 工具调用事件
- `ContentEvent` - 内容输出事件
- `AgentActivityEvent` - Agent 活动事件

### 工具调用 (tool_call.py)

- `ToolCallRequest` - 工具调用请求
- `ToolResult` - 工具执行结果
- `ToolConfirmationDetails` - 确认详情

## 📊 状态流转

```
SUBMITTED → WORKING → INPUT_REQUIRED → WORKING → COMPLETED
                  ↘               ↙
                    FAILED / CANCELLED
```

## 🎯 使用示例

```python
from core.schema import (
    TaskState,
    Message,
    ToolCallRequest,
    ToolResult,
)

# 创建用户消息
msg = Message.user_message("起飞到50米高度")

# 创建工具调用
request = ToolCallRequest(
    name="device_tool.takeoff",
    args={"uav_id": "uav_1", "altitude": 50}
)

# 创建工具结果
result = ToolResult.success_result(
    call_id=request.call_id,
    content="UAV uav_1 正在起飞到 50m",
    display="✅ 起飞指令已发送"
)
```

