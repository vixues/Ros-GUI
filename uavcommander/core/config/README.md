# Config 模块

> ⚙️ 配置管理层

本模块管理 UAV Commander 系统的所有配置项。

## 📁 模块结构

```
config/
├── __init__.py          # 模块导出
├── settings.py          # 全局系统设置
├── llm_config.py        # LLM 配置
├── safety_policy.py     # 安全策略配置
├── ros_params.py        # ROS 参数配置
└── README.md            # 本文档
```

## 🔧 配置项

### 系统设置 (settings.py)

```python
from core.config import Config, ApprovalMode

config = Config()
config.system.environment = Environment.SIMULATION
config.system.approval_mode = ApprovalMode.YOLO  # 仿真模式
```

#### 环境类型
- `DEVELOPMENT` - 开发环境
- `TESTING` - 测试环境
- `SIMULATION` - 仿真环境
- `PRODUCTION` - 生产环境

#### 审批模式
- `STRICT` - 所有操作需确认
- `NORMAL` - 仅危险操作需确认（默认）
- `YOLO` - 自动批准（仅限仿真）

### LLM 配置 (llm_config.py)

```python
from core.config import LLMSettings, LLMProvider

llm_settings = LLMSettings(
    default_model="gpt-4",
    openai_api_key="sk-xxx",
)
```

#### 支持的 LLM
- OpenAI (GPT-4, GPT-4-Turbo, GPT-4o)
- Anthropic (Claude-3-Opus, Claude-3-Sonnet)
- Google (Gemini-Pro, Gemini-1.5-Pro)
- Azure OpenAI
- 本地模型

### 安全策略 (safety_policy.py)

```python
from core.config import SafetyPolicy, OperationLimits, GeofenceZone

policy = SafetyPolicy(
    limits=OperationLimits(
        max_altitude=120.0,
        max_speed=15.0,
        min_battery_level=20.0,
    )
)
```

#### 风险等级
- `LOW` - 低风险（查询操作）
- `MEDIUM` - 中风险（移动操作）
- `HIGH` - 高风险（起飞/编队）
- `CRITICAL` - 危急（紧急操作）

### ROS 配置 (ros_params.py)

```python
from core.config import ROSSettings, UAVConfig, SwarmConfig

ros_settings = ROSSettings(
    distro=ROSDistro.HUMBLE,
    node_name="uav_commander",
    simulation_mode=True,
)
```

## 🌍 环境变量

系统支持通过环境变量配置：

```bash
# 系统配置
export UAV_ENVIRONMENT=simulation
export UAV_APPROVAL_MODE=yolo
export UAV_DEBUG=true
export UAV_LOG_LEVEL=DEBUG

# LLM 配置
export OPENAI_API_KEY=sk-xxx
export ANTHROPIC_API_KEY=xxx
export UAV_DEFAULT_MODEL=gpt-4

# ROS 配置
export ROS_DISTRO=humble
export ROS_DOMAIN_ID=0
export UAV_SIMULATION=true
```

## 📊 配置加载优先级

1. 代码中直接设置
2. 配置文件 (config.yaml)
3. 环境变量
4. 默认值

## 🎯 使用示例

```python
from core.config import get_config, get_safety_policy

# 获取全局配置
config = get_config()
print(f"当前模型: {config.get_model()}")
print(f"审批模式: {config.get_approval_mode()}")

# 检查安全策略
policy = get_safety_policy()
action, msg = policy.validate_operation(
    "device_tool.takeoff",
    {"altitude": 50}
)
```

