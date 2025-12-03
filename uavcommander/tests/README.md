# 测试模块

> 🧪 UAV Commander 单元测试和集成测试

## 📁 结构

```
tests/
├── __init__.py          # 测试模块初始化
├── conftest.py          # Pytest fixtures
├── test_tools.py        # 工具测试
├── test_agent.py        # Agent 测试
└── README.md            # 本文档
```

## 🚀 运行测试

### 运行所有测试

```bash
pytest
```

### 运行特定测试文件

```bash
pytest tests/test_tools.py
```

### 运行带覆盖率报告

```bash
pytest --cov=core --cov=cli --cov=utils --cov-report=html
```

### 运行异步测试

```bash
pytest -v tests/test_agent.py
```

## 📊 测试覆盖

| 模块 | 覆盖范围 |
|------|----------|
| `core.tools` | DeviceTool, SwarmTool, Registry |
| `core.agent` | Context, Registry, MockLLM |
| `core.schema` | 数据结构验证 |

## 🔧 Fixtures

### test_config

测试环境配置，自动批准所有操作。

```python
def test_something(test_config):
    assert test_config.get_approval_mode() == ApprovalMode.YOLO
```

### simulation_config

仿真环境配置。

```python
def test_simulation(simulation_config):
    assert simulation_config.is_simulation()
```

## 📝 编写测试

### 异步测试

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

### 使用 Fixture

```python
class TestDeviceTool:
    @pytest.fixture
    def device_tool(self):
        return DeviceTool()
    
    @pytest.mark.asyncio
    async def test_arm(self, device_tool):
        result = await device_tool.arm(uav_id="uav_1")
        assert result.success
```

