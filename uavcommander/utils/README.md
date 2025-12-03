# Utils 模块

> 🔧 通用工具函数库

本模块提供 UAV Commander 系统的通用工具函数和辅助类。

## 📁 模块结构

```
utils/
├── __init__.py          # 模块导出
├── logging.py           # 日志系统
├── event_bus.py         # 事件总线
├── async_utils.py       # 异步工具
└── README.md            # 本文档
```

## 🔧 核心组件

### 日志系统 (logging.py)

```python
from utils import setup_logging, get_logger, LogConfig, LogLevel

# 配置日志
config = LogConfig(
    level=LogLevel.DEBUG,
    console_colors=True,
    file_enabled=True,
)
setup_logging(config)

# 使用日志
logger = get_logger("my_module")
logger.info("Hello, UAV Commander!")
```

#### 日志格式
- `SIMPLE` - 简单格式
- `DETAILED` - 详细格式（含文件名和行号）
- `JSON` - JSON 格式（用于日志分析）

#### 专用日志器
```python
from utils import TaskLogger, AgentLogger

# 任务日志
task_logger = TaskLogger("task_123")
task_logger.info("任务开始")

# Agent 日志
agent_logger = AgentLogger("coordinator", "task_123")
agent_logger.tool_call("takeoff", {"altitude": 50})
```

### 事件总线 (event_bus.py)

```python
from utils import EventBus, get_event_bus
from core.schema import EventType, TaskEvent

# 获取全局事件总线
bus = get_event_bus()

# 订阅事件
@bus.on(EventType.TASK_STATE_CHANGE)
def on_task_change(event):
    print(f"任务状态变更: {event.state}")

# 发布事件
bus.publish(TaskEvent(
    event_type=EventType.TASK_STATE_CHANGE,
    task_id="task_123",
    state=TaskState.WORKING,
))
```

#### 订阅选项
```python
# 优先级订阅（数字越大越先执行）
bus.subscribe(EventType.ERROR, handler, priority=100)

# 一次性订阅
bus.subscribe(EventType.TASK_COMPLETED, handler, once=True)

# 带过滤器的订阅
bus.subscribe(
    EventType.TOOL_CALL_COMPLETED,
    handler,
    filter_func=lambda e: e.tool_name == "takeoff"
)
```

### 异步工具 (async_utils.py)

```python
from utils import (
    AsyncTimeout,
    retry_async,
    RetryConfig,
    AsyncLock,
    TaskGroup,
    gather_with_concurrency,
)

# 超时控制
async with AsyncTimeout(10.0, "操作超时"):
    result = await long_operation()

# 重试机制
config = RetryConfig(max_retries=3, exponential_backoff=True)
result = await retry_async(unstable_operation, config=config)

# 任务组
group = TaskGroup("my_tasks")
group.add("task1", async_task_1())
group.add("task2", async_task_2())
results, errors = await group.wait_all(timeout=30.0)

# 并发限制
results = await gather_with_concurrency(
    5,  # 最大并发数
    *[process(item) for item in items]
)
```

## 🎯 使用示例

### 完整日志配置

```python
from utils import setup_logging, LogConfig, LogLevel, LogFormat
from pathlib import Path

config = LogConfig(
    level=LogLevel.DEBUG,
    format=LogFormat.DETAILED,
    console_enabled=True,
    console_colors=True,
    file_enabled=True,
    file_path=Path("logs/uav_commander.log"),
    file_max_size=10 * 1024 * 1024,  # 10MB
    file_backup_count=5,
    json_file_enabled=True,
    json_file_path=Path("logs/uav_commander.jsonl"),
)

setup_logging(config)
```

### 事件驱动架构

```python
from utils import EventBus, TaskEventBus
from core.schema import EventType

# 创建任务级事件总线
task_bus = TaskEventBus("task_123")

# 异步启动事件处理
await task_bus.start()

# 发送事件到队列
task_bus.emit(event)

# 停止事件处理
await task_bus.stop()
```

### 可靠的异步操作

```python
from utils import retry_async, AsyncLock, AsyncSemaphore

# 分布式锁
lock = AsyncLock("resource_lock")
async with lock:
    await modify_shared_resource()

# 并发控制
semaphore = AsyncSemaphore(5, "api_limiter")
async with semaphore:
    await call_external_api()
```

