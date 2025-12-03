"""
工具模块测试
"""

import pytest
import asyncio

from core.tools import (
    DeviceTool,
    SwarmTool,
    get_tool_registry,
    setup_default_tools,
)


class TestDeviceTool:
    """DeviceTool 测试"""
    
    @pytest.fixture
    def device_tool(self):
        return DeviceTool()
    
    @pytest.mark.asyncio
    async def test_arm(self, device_tool):
        """测试解锁"""
        result = await device_tool.arm(uav_id="uav_1")
        assert result.success
        assert "uav_1" in result.display_content
    
    @pytest.mark.asyncio
    async def test_takeoff(self, device_tool):
        """测试起飞"""
        # 先解锁
        await device_tool.arm(uav_id="uav_1")
        
        # 起飞
        result = await device_tool.takeoff(uav_id="uav_1", altitude=50)
        assert result.success
        assert "50" in result.display_content
    
    @pytest.mark.asyncio
    async def test_takeoff_without_arm(self, device_tool):
        """测试未解锁起飞"""
        result = await device_tool.takeoff(uav_id="uav_2", altitude=50)
        assert not result.success
        assert "未解锁" in result.error
    
    @pytest.mark.asyncio
    async def test_get_status(self, device_tool):
        """测试获取状态"""
        result = await device_tool.get_status(uav_id="uav_1")
        assert result.success
        assert result.metadata is not None
        assert "uav_id" in result.metadata
    
    @pytest.mark.asyncio
    async def test_get_battery(self, device_tool):
        """测试获取电量"""
        result = await device_tool.get_battery(uav_id="uav_1")
        assert result.success
        assert "percent" in result.metadata


class TestSwarmTool:
    """SwarmTool 测试"""
    
    @pytest.fixture
    def swarm_tool(self):
        return SwarmTool()
    
    @pytest.mark.asyncio
    async def test_form_formation(self, swarm_tool):
        """测试建立编队"""
        result = await swarm_tool.form_formation(
            formation_type="v_shape",
            uav_ids=["uav_1", "uav_2", "uav_3"],
            target_lat=31.2,
            target_lon=121.5,
            target_alt=50,
            spacing=10.0,
        )
        assert result.success
        assert "v_shape" in result.display_content
        assert result.metadata["uav_count"] == 3
    
    @pytest.mark.asyncio
    async def test_form_formation_min_uavs(self, swarm_tool):
        """测试编队最少无人机数"""
        result = await swarm_tool.form_formation(
            formation_type="line",
            uav_ids=["uav_1"],  # 只有1架
            target_lat=31.2,
            target_lon=121.5,
            target_alt=50,
        )
        assert not result.success
        assert "至少需要2架" in result.error
    
    @pytest.mark.asyncio
    async def test_disperse(self, swarm_tool):
        """测试散开编队"""
        result = await swarm_tool.disperse(
            uav_ids=["uav_1", "uav_2", "uav_3"],
            radius=50.0,
        )
        assert result.success
    
    @pytest.mark.asyncio
    async def test_get_swarm_status(self, swarm_tool):
        """测试获取集群状态"""
        result = await swarm_tool.get_swarm_status()
        assert result.success


class TestToolRegistry:
    """工具注册表测试"""
    
    def test_setup_default_tools(self):
        """测试默认工具注册"""
        setup_default_tools()
        registry = get_tool_registry()
        
        # 检查工具是否注册
        device_tool = registry.get("device_tool")
        assert device_tool is not None
        
        swarm_tool = registry.get("swarm_tool")
        assert swarm_tool is not None
    
    def test_get_schemas(self):
        """测试获取 Schema"""
        setup_default_tools()
        registry = get_tool_registry()
        
        schemas = registry.get_all_schemas()
        assert len(schemas) > 0
        
        # 检查 Schema 格式
        for schema in schemas:
            assert schema.name
            assert schema.description

