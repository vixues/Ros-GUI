# Tools 模块

> 🔧 UAV Commander 工具层

本模块实现了无人机控制的各类工具，包括单机控制、集群控制等。

## 📁 模块结构

```
tools/
├── __init__.py          # 模块导出
├── tools.py             # 声明式工具基类
├── tool_registry.py     # 工具注册表
├── device_tool.py       # 单机控制工具
├── swarm_tool.py        # 集群控制工具
└── README.md            # 本文档
```

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                     ToolRegistry                             │
│  (工具注册、发现、查询)                                       │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
┌─────────────────┐ ┌───────────────┐ ┌─────────────────┐
│   DeviceTool    │ │  SwarmTool    │ │   SafetyTool    │
│  (单机控制)     │ │  (集群控制)   │ │   (安全控制)    │
└─────────────────┘ └───────────────┘ └─────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                    ToolInvocation                            │
│  (工具调用实例)                                              │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 核心组件

### DeclarativeTool

声明式工具基类，定义工具的统一接口。

```python
from core.tools import DeclarativeTool, ToolMethod, ToolCategory

class MyTool(DeclarativeTool):
    name = "my_tool"
    description = "我的自定义工具"
    category = ToolCategory.DEVICE
    
    def _setup_methods(self):
        self.register_method(ToolMethod(
            name="my_action",
            description="执行某个动作",
            parameters={
                "param1": {"type": "string", "description": "参数1"},
            },
            required=["param1"],
        ))
    
    async def my_action(self, param1: str) -> ToolResult:
        # 实现逻辑
        return ToolResult.success_result("", "完成", "✅ 完成")
```

### ToolRegistry

工具注册表，管理所有可用工具。

```python
from core.tools import get_tool_registry, register_tool

# 获取注册表
registry = get_tool_registry()

# 注册工具
register_tool(MyTool())

# 获取工具
tool = registry.get("my_tool")

# 获取所有 Schema
schemas = registry.get_schemas_for_llm()
```

### DeviceTool

单机控制工具，提供对单架无人机的基本操作。

```python
from core.tools import DeviceTool

device = DeviceTool()

# 起飞
result = await device.takeoff(uav_id="uav_1", altitude=50)

# 飞往位置
result = await device.goto(
    uav_id="uav_1",
    lat=31.2,
    lon=121.5,
    alt=50,
    speed=5.0
)

# 获取状态
result = await device.get_status(uav_id="uav_1")
```

#### 可用方法

| 方法 | 描述 | 危险等级 |
|------|------|----------|
| `arm` | 解锁电机 | 高 |
| `disarm` | 锁定电机 | 低 |
| `takeoff` | 起飞 | 高 |
| `land` | 降落 | 低 |
| `goto` | 飞往位置 | 高 |
| `set_velocity` | 设置速度 | 高 |
| `get_status` | 获取状态 | 无 |
| `get_position` | 获取位置 | 无 |
| `get_battery` | 获取电量 | 无 |

### SwarmTool

集群控制工具，提供多机协同操作。

```python
from core.tools import SwarmTool

swarm = SwarmTool()

# 建立 V 形编队
result = await swarm.form_formation(
    formation_type="v_shape",
    uav_ids=["uav_1", "uav_2", "uav_3", "uav_4", "uav_5"],
    target_lat=31.2,
    target_lon=121.5,
    target_alt=50,
    spacing=10.0
)

# 散开编队
result = await swarm.disperse(
    uav_ids=["uav_1", "uav_2", "uav_3"],
    radius=50.0
)
```

#### 编队类型

| 类型 | 描述 | 适用场景 |
|------|------|----------|
| `line` | 线形 | 侦察 |
| `v_shape` | V形 | 长距离巡航 |
| `circle` | 圆形 | 区域监控 |
| `diamond` | 菱形 | 突防 |
| `wedge` | 楔形 | 进攻 |
| `grid` | 网格 | 搜索 |

## 🎯 使用示例

### 初始化工具

```python
from core.tools import setup_default_tools, get_tool_registry

# 设置默认工具
setup_default_tools()

# 获取注册表
registry = get_tool_registry()

# 列出所有工具
for tool in registry.list_tools():
    print(f"- {tool.name}: {tool.description}")
```

### 执行工具调用

```python
from core.schema import ToolCallRequest
from core.tools import get_tool_registry

registry = get_tool_registry()

# 创建调用请求
request = ToolCallRequest(
    name="device_tool.takeoff",
    args={"uav_id": "uav_1", "altitude": 50}
)

# 构建调用
invocation = registry.build_invocation(request)

if invocation:
    # 检查是否需要确认
    if invocation.requires_confirmation:
        print("此操作需要确认！")
    
    # 执行
    result = await invocation.execute()
    print(result.display_content)
```

### 自定义工具

```python
from core.tools import DeclarativeTool, ToolMethod, ToolCategory, register_tool
from core.schema import ToolResult

class CameraTool(DeclarativeTool):
    name = "camera_tool"
    description = "无人机摄像头控制"
    category = ToolCategory.SENSOR
    
    def _setup_methods(self):
        self.register_method(ToolMethod(
            name="take_photo",
            description="拍照",
            parameters={
                "uav_id": {"type": "string", "description": "无人机ID"},
            },
            required=["uav_id"],
        ))
        
        self.register_method(ToolMethod(
            name="start_video",
            description="开始录像",
            parameters={
                "uav_id": {"type": "string", "description": "无人机ID"},
                "duration": {"type": "number", "description": "录制时长(秒)"},
            },
            required=["uav_id"],
        ))
    
    async def take_photo(self, uav_id: str) -> ToolResult:
        # 实现拍照逻辑
        return ToolResult.success_result(
            "",
            f"无人机 {uav_id} 拍照成功",
            f"📷 {uav_id} 拍照完成"
        )
    
    async def start_video(self, uav_id: str, duration: int = 30) -> ToolResult:
        # 实现录像逻辑
        return ToolResult.success_result(
            "",
            f"无人机 {uav_id} 开始录像 {duration}秒",
            f"🎥 {uav_id} 录像中..."
        )

# 注册工具
register_tool(CameraTool())
```

## ⚡ 性能考虑

1. **工具缓存**: 工具实例被缓存，避免重复创建
2. **异步执行**: 所有工具方法都是异步的
3. **并发控制**: 通过调度器控制并发数量

