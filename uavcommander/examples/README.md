# 示例代码

> 📚 UAV Commander 使用示例

## 📁 示例列表

### basic_usage.py

基础使用示例，展示：
- 单机控制（起飞、飞行、降落）
- 集群控制（编队、同步动作）
- 工具注册表使用
- Agent 注册表使用

```bash
python examples/basic_usage.py
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp env.example .env
# 编辑 .env 填入 API Key
```

### 3. 运行示例

```bash
python examples/basic_usage.py
```

## 📖 代码示例

### 单机控制

```python
from core.tools import DeviceTool

device = DeviceTool()

# 起飞
await device.arm(uav_id="uav_1")
await device.takeoff(uav_id="uav_1", altitude=50)

# 飞行
await device.goto(uav_id="uav_1", lat=31.2, lon=121.5, alt=50)

# 降落
await device.land(uav_id="uav_1")
```

### 集群控制

```python
from core.tools import SwarmTool

swarm = SwarmTool()

# V形编队
await swarm.form_formation(
    formation_type="v_shape",
    uav_ids=["uav_1", "uav_2", "uav_3"],
    target_lat=31.2,
    target_lon=121.5,
    target_alt=50,
)

# 同步降落
await swarm.sync_action(
    uav_ids=["uav_1", "uav_2", "uav_3"],
    action="land"
)
```

### Agent 对话

```python
from core.agent import AgentExecutorFactory
from core.tools import setup_default_tools

setup_default_tools()

factory = AgentExecutorFactory()
executor = factory.create_coordinator()

result = await executor.run("让3架无人机起飞并建立编队")
print(result.content)
```

