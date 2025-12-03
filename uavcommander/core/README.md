# Core 模块

> 🎯 UAV Commander 核心模块

本目录包含 UAV Commander 的所有核心功能实现。

## 📁 目录结构

```
core/
├── __init__.py          # 模块导出
├── schema/              # 数据模式定义
│   ├── task_state.py    # 任务状态
│   ├── messages.py      # 消息类型
│   ├── events.py        # 事件类型
│   └── tool_call.py     # 工具调用类型
│
├── config/              # 配置管理
│   ├── settings.py      # 全局设置
│   ├── llm_config.py    # LLM 配置
│   ├── safety_policy.py # 安全策略
│   └── ros_params.py    # ROS 参数
│
├── agent/               # Agent 系统
│   ├── basellm.py       # LLM 抽象基类
│   ├── llm.py           # LLM 实现
│   ├── context.py       # 上下文管理
│   ├── registry.py      # Agent 注册表
│   ├── prompts.py       # Prompt 模板
│   ├── scheduler.py     # 工具调度器
│   ├── invocation.py    # 子代理容器
│   ├── executor.py      # Agent 执行器
│   ├── automator.py     # 自动执行逻辑
│   └── task.py          # 任务状态机
│
└── tools/               # 工具层
    ├── tools.py         # 声明式工具基类
    ├── tool_registry.py # 工具注册表
    ├── device_tool.py   # 单机控制工具
    └── swarm_tool.py    # 集群控制工具
```

## 🔧 模块说明

### Schema 模块

定义系统中使用的所有数据结构：

- **TaskState**: 任务生命周期状态
- **Message**: 对话消息格式
- **Event**: 事件驱动通信
- **ToolCall**: 工具调用相关类型

### Config 模块

管理系统配置：

- **SystemSettings**: 全局系统设置
- **LLMSettings**: LLM 提供商配置
- **SafetyPolicy**: 安全策略定义
- **ROSSettings**: ROS 2 通信参数

### Agent 模块

核心 Agent 系统实现：

- **AgentExecutor**: 驱动 Agent 运行主循环
- **CoreToolScheduler**: 工具调度中枢
- **SubagentInvocation**: 子代理执行容器
- **Context**: 对话上下文管理

### Tools 模块

工具层实现：

- **DeviceTool**: 单机控制（arm, takeoff, land, goto...）
- **SwarmTool**: 集群控制（formation, disperse, sync...）

## 🚀 快速使用

```python
from core.config import get_config
from core.agent import AgentExecutorFactory
from core.tools import setup_default_tools

# 设置工具
setup_default_tools()

# 创建执行器
factory = AgentExecutorFactory()
executor = factory.create_coordinator()

# 执行命令
result = await executor.run("让3架无人机起飞")
print(result.content)
```

## 📚 详细文档

每个子模块都有独立的 README：

- [Schema 模块](schema/README.md)
- [Config 模块](config/README.md)
- [Agent 模块](agent/README.md)
- [Tools 模块](tools/README.md)

