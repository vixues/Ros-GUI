# Agent 模块

> 🧠 UAV Commander 核心 Agent 系统

本模块实现了基于 LLM 的 Multi-Agent 编排系统，是 UAV Commander 的核心组件。

## 📁 模块结构

```
agent/
├── __init__.py          # 模块导出
├── basellm.py           # LLM 抽象基类
├── llm.py               # LLM 具体实现
├── context.py           # 上下文管理
├── registry.py          # Agent 注册表
├── prompts.py           # Prompt 模板
├── scheduler.py         # 工具调度器
├── invocation.py        # 子代理执行容器
├── executor.py          # Agent 执行器
├── automator.py         # 自动执行逻辑
├── task.py              # 任务状态机
└── README.md            # 本文档
```

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                      Automator                               │
│  (多轮对话驱动, 任务完成判断)                                 │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                    AgentExecutor                             │
│  (Agent 主循环: LLM推理 → 工具调用 → 结果反馈)                │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
┌─────────────────┐ ┌───────────┐ ┌─────────────────┐
│ CoreToolScheduler│ │   LLM     │ │    Context      │
│ (工具生命周期)   │ │ (推理引擎) │ │  (对话历史)     │
└────────┬────────┘ └───────────┘ └─────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│              SubagentInvocation                              │
│  (子代理封装为工具, 流式活动传递)                             │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 核心组件

### 1. AgentExecutor

Agent 执行器，驱动 Agent 运行的主循环。

```python
from core.agent import AgentExecutor, AgentExecutorFactory

# 使用工厂创建
factory = AgentExecutorFactory()
executor = factory.create_coordinator()

# 运行
result = await executor.run("让3架无人机起飞")
print(result.content)
```

### 2. CoreToolScheduler

工具调度器，管理工具调用的完整生命周期。

```python
状态流转:
Scheduled → Executing → Success / Error / Cancelled
                ↓
        Awaiting_Approval (需要确认时)
```

### 3. SubagentInvocation

子代理执行容器，将 Agent 封装为可调用工具。

```python
from core.agent import SubagentInvocationBuilder

builder = SubagentInvocationBuilder(config)
invocation = builder.build(
    agent_name="formation_agent",
    task="建立V形编队",
    context={"uav_ids": ["uav_1", "uav_2", "uav_3"]}
)

result = await invocation.execute(update_output=print)
```

### 4. Context

上下文管理器，维护对话历史和上下文压缩。

```python
from core.agent import Context, ContextConfig

context = Context(config=ContextConfig(
    max_messages=100,
    auto_compress=True,
))

context.add_user_message("起飞")
context.add_assistant_message("正在执行起飞...")

# 获取 LLM 格式消息
messages = context.get_llm_messages()
```

### 5. AgentRegistry

Agent 注册表，管理 Agent 定义。

```python
from core.agent import (
    AgentRegistry,
    AgentDefinition,
    AgentType,
    AgentCapability,
)

# 注册自定义 Agent
registry = get_agent_registry()
registry.register(AgentDefinition(
    name="my_agent",
    description="自定义代理",
    agent_type=AgentType.SPECIALIST,
    system_prompt="你是一个专业助手...",
    tools=["device_tool"],
    capabilities=[AgentCapability.TOOL_USE],
))
```

## 🎯 使用示例

### 基础使用

```python
import asyncio
from core.agent import AgentExecutorFactory

async def main():
    factory = AgentExecutorFactory()
    executor = factory.create_coordinator()
    
    # 注册回调
    executor.on_output(lambda msg: print(f"[Output] {msg}"))
    
    # 执行
    result = await executor.run("查看所有无人机状态")
    
    print(f"成功: {result.success}")
    print(f"响应: {result.content}")
    print(f"工具调用: {result.tool_calls_count}")

asyncio.run(main())
```

### 自动多轮对话

```python
from core.agent import AutomatorFactory, AutomatorConfig

async def main():
    factory = AutomatorFactory()
    automator = factory.create_default(
        AutomatorConfig(
            max_auto_turns=10,
            require_confirmation=False,
        )
    )
    
    result = await automator.run("让5架无人机编队飞往A点，然后展开搜索")
    
    print(f"轮次: {result.turns}")
    print(f"工具调用: {result.total_tool_calls}")
    print(f"最终响应: {result.final_response}")
```

### 流式输出

```python
from core.agent import AgentExecutor, StreamEvent, StreamEventType

executor = AgentExecutor(agent_def, config)

def handle_stream(event: StreamEvent):
    if event.type == StreamEventType.CONTENT:
        print(event.content, end="", flush=True)
    elif event.type == StreamEventType.TOOL_CALL:
        print(f"\n[调用工具] {event.tool_call.name}")

executor.on_stream_event(handle_stream)
```

## 📊 预定义 Agent

| Agent | 类型 | 描述 |
|-------|------|------|
| `coordinator` | Coordinator | 主协调代理，理解意图并调度 |
| `formation_agent` | Specialist | 编队控制专家 |
| `navigation_agent` | Specialist | 导航规划专家 |
| `search_agent` | Specialist | 搜索任务专家 |

## 🔌 LLM 支持

- **OpenAI**: GPT-4, GPT-4-Turbo, GPT-4o
- **Anthropic**: Claude-3-Opus, Claude-3-Sonnet
- **Google**: Gemini-Pro, Gemini-1.5-Pro
- **Local**: 模拟 LLM（测试用）

```python
from core.agent import create_llm
from core.config import LLMProvider

# 创建 OpenAI LLM
llm = create_llm(provider=LLMProvider.OPENAI, model_name="gpt-4")

# 创建 Claude LLM
llm = create_llm(provider=LLMProvider.ANTHROPIC, model_name="claude-3-opus")
```

## ⚡ 性能优化

1. **流式输出**: 减少首字延迟
2. **上下文压缩**: 自动压缩长对话
3. **并发工具调用**: 多工具并行执行
4. **信号量控制**: 限制并发数量
