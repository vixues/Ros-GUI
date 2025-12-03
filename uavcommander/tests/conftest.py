"""
Pytest 配置和 fixtures
"""

import pytest
import asyncio
from typing import Generator

from core.config import Config, SystemSettings, ApprovalMode, Environment, set_config


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_config() -> Config:
    """测试配置"""
    settings = SystemSettings(
        environment=Environment.TESTING,
        debug=True,
        approval_mode=ApprovalMode.YOLO,  # 测试时自动批准
    )
    config = Config(system=settings)
    set_config(config)
    return config


@pytest.fixture
def simulation_config() -> Config:
    """仿真配置"""
    settings = SystemSettings(
        environment=Environment.SIMULATION,
        debug=False,
        approval_mode=ApprovalMode.YOLO,
    )
    config = Config(system=settings)
    set_config(config)
    return config

