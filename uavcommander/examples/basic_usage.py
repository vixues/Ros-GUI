"""
基础使用示例

展示 UAV Commander 的基本用法。
"""

import asyncio
from core.config import Config, SystemSettings, ApprovalMode, Environment, set_config
from core.tools import DeviceTool, SwarmTool, setup_default_tools, get_tool_registry
from core.agent import AgentExecutorFactory, get_agent_registry
from utils import setup_logging, LogConfig, LogLevel


async def example_device_control():
    """单机控制示例"""
    print("=" * 60)
    print("单机控制示例")
    print("=" * 60)
    
    # 创建设备工具
    device = DeviceTool()
    
    # 获取状态
    print("\n1. 获取无人机状态")
    result = await device.get_status(uav_id="uav_1")
    print(f"   {result.display_content}")
    
    # 解锁
    print("\n2. 解锁无人机")
    result = await device.arm(uav_id="uav_1")
    print(f"   {result.display_content}")
    
    # 起飞
    print("\n3. 起飞到 50 米")
    result = await device.takeoff(uav_id="uav_1", altitude=50)
    print(f"   {result.display_content}")
    
    # 飞往目标
    print("\n4. 飞往目标位置")
    result = await device.goto(
        uav_id="uav_1",
        lat=31.2345,
        lon=121.4567,
        alt=50,
        speed=5.0
    )
    print(f"   {result.display_content}")
    
    # 降落
    print("\n5. 降落")
    result = await device.land(uav_id="uav_1")
    print(f"   {result.display_content}")


async def example_swarm_control():
    """集群控制示例"""
    print("\n" + "=" * 60)
    print("集群控制示例")
    print("=" * 60)
    
    # 创建集群工具
    swarm = SwarmTool()
    
    # 建立编队
    print("\n1. 建立 V 形编队")
    result = await swarm.form_formation(
        formation_type="v_shape",
        uav_ids=["uav_1", "uav_2", "uav_3", "uav_4", "uav_5"],
        target_lat=31.2345,
        target_lon=121.4567,
        target_alt=50,
        spacing=10.0
    )
    print(f"   {result.display_content}")
    
    # 获取集群状态
    print("\n2. 获取集群状态")
    result = await swarm.get_swarm_status()
    print(f"   {result.display_content}")
    
    # 同步动作
    print("\n3. 同步悬停")
    result = await swarm.sync_action(
        uav_ids=["uav_1", "uav_2", "uav_3", "uav_4", "uav_5"],
        action="hover"
    )
    print(f"   {result.display_content}")
    
    # 散开
    print("\n4. 散开编队")
    result = await swarm.disperse(
        uav_ids=["uav_1", "uav_2", "uav_3", "uav_4", "uav_5"],
        radius=100.0
    )
    print(f"   {result.display_content}")


async def example_agent_executor():
    """Agent 执行器示例"""
    print("\n" + "=" * 60)
    print("Agent 执行器示例")
    print("=" * 60)
    
    # 设置工具
    setup_default_tools()
    
    # 创建执行器
    factory = AgentExecutorFactory()
    executor = factory.create_coordinator()
    
    if not executor:
        print("无法创建执行器（可能缺少 LLM API Key）")
        return
    
    # 注册输出回调
    def on_output(msg: str):
        print(f"   [输出] {msg}")
    
    executor.on_output(on_output)
    
    # 执行命令
    print("\n执行命令: 查看所有无人机状态")
    try:
        result = await executor.run("查看所有无人机状态")
        print(f"\n结果: {result.content}")
    except Exception as e:
        print(f"执行失败: {e}")


async def example_tool_registry():
    """工具注册表示例"""
    print("\n" + "=" * 60)
    print("工具注册表示例")
    print("=" * 60)
    
    # 设置默认工具
    setup_default_tools()
    
    # 获取注册表
    registry = get_tool_registry()
    
    # 列出所有工具
    print("\n已注册工具:")
    for tool in registry.list_tools():
        print(f"  - {tool.name}: {tool.description}")
        for method in tool.get_methods():
            dangerous = " ⚠️" if method.dangerous else ""
            print(f"      • {method.name}{dangerous}: {method.description}")


async def example_agent_registry():
    """Agent 注册表示例"""
    print("\n" + "=" * 60)
    print("Agent 注册表示例")
    print("=" * 60)
    
    # 获取注册表
    registry = get_agent_registry()
    
    # 列出所有代理
    print("\n已注册代理:")
    for name in registry.list_agents():
        agent = registry.get(name)
        if agent:
            print(f"  - {name} ({agent.agent_type.value})")
            print(f"      描述: {agent.description}")
            if agent.tools:
                print(f"      工具: {', '.join(agent.tools)}")


async def main():
    """主函数"""
    # 配置日志
    setup_logging(LogConfig(level=LogLevel.WARNING))
    
    # 配置系统（仿真模式 + YOLO 审批）
    settings = SystemSettings(
        environment=Environment.SIMULATION,
        approval_mode=ApprovalMode.YOLO,
    )
    config = Config(system=settings)
    set_config(config)
    
    print("🚁 UAV Commander 示例")
    print("=" * 60)
    
    # 运行示例
    await example_device_control()
    await example_swarm_control()
    await example_tool_registry()
    await example_agent_registry()
    
    # Agent 执行器示例需要 API Key
    # await example_agent_executor()
    
    print("\n" + "=" * 60)
    print("示例完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

