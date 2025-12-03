"""
Agent 注册表模块

管理 Agent 定义的注册与发现。
"""

from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging

from core.schema import ToolSchema

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Agent 类型"""
    
    COORDINATOR = "coordinator"  # 协调器（主代理）
    SPECIALIST = "specialist"    # 专家（子代理）
    WORKER = "worker"           # 工作者


class AgentCapability(Enum):
    """Agent 能力"""
    
    # 基础能力
    CHAT = "chat"
    TOOL_USE = "tool_use"
    PLANNING = "planning"
    
    # 无人机相关
    FORMATION = "formation"
    NAVIGATION = "navigation"
    SEARCH = "search"
    MONITORING = "monitoring"
    
    # 高级能力
    MULTI_AGENT = "multi_agent"
    LONG_RUNNING = "long_running"


@dataclass
class AgentDefinition:
    """Agent 定义"""
    
    name: str
    description: str
    agent_type: AgentType = AgentType.SPECIALIST
    
    # 系统提示词
    system_prompt: str = ""
    
    # 可用工具
    tools: List[str] = field(default_factory=list)
    
    # 能力列表
    capabilities: List[AgentCapability] = field(default_factory=list)
    
    # 配置
    model: Optional[str] = None
    max_turns: int = 20
    timeout_seconds: float = 300.0
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_tool_schema(self) -> ToolSchema:
        """转换为工具 Schema（用于子代理调用）"""
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters={
                "task": {
                    "type": "string",
                    "description": "要执行的任务描述",
                },
                "context": {
                    "type": "object",
                    "description": "任务上下文信息",
                },
            },
            required=["task"],
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "agent_type": self.agent_type.value,
            "system_prompt": self.system_prompt,
            "tools": self.tools,
            "capabilities": [c.value for c in self.capabilities],
            "model": self.model,
            "max_turns": self.max_turns,
            "timeout_seconds": self.timeout_seconds,
            "metadata": self.metadata,
        }


# 预定义 Agent
PREDEFINED_AGENTS: Dict[str, AgentDefinition] = {
    "coordinator": AgentDefinition(
        name="coordinator",
        description="主协调代理，负责理解用户意图并调度子代理执行任务",
        agent_type=AgentType.COORDINATOR,
        system_prompt="你是 UAV Commander 的主协调代理，负责理解用户的无人机控制意图并调度执行。",
        tools=["formation_agent", "navigation_agent", "search_agent", "device_tool", "swarm_tool"],
        capabilities=[
            AgentCapability.CHAT,
            AgentCapability.TOOL_USE,
            AgentCapability.PLANNING,
            AgentCapability.MULTI_AGENT,
        ],
    ),
    "formation_agent": AgentDefinition(
        name="formation_agent",
        description="编队控制专家，负责计算编队参数、分配槽位、协调编队飞行",
        agent_type=AgentType.SPECIALIST,
        system_prompt="""你是编队控制专家，负责无人机编队任务。
你的能力包括：
- 计算各种编队类型的位置参数（V形、线形、圆形等）
- 为每架无人机分配编队槽位
- 协调编队的形成和变换
- 处理编队飞行中的同步问题

可用工具：swarm_tool.form_formation, device_tool.goto, device_tool.get_status
""",
        tools=["swarm_tool", "device_tool"],
        capabilities=[
            AgentCapability.TOOL_USE,
            AgentCapability.FORMATION,
        ],
    ),
    "navigation_agent": AgentDefinition(
        name="navigation_agent",
        description="导航规划专家，负责路径规划、避障处理、轨迹优化",
        agent_type=AgentType.SPECIALIST,
        system_prompt="""你是导航规划专家，负责无人机的路径规划任务。
你的能力包括：
- 规划从起点到终点的飞行路径
- 考虑障碍物进行避障
- 优化飞行轨迹以提高效率
- 处理多机路径冲突

可用工具：device_tool.goto, device_tool.get_position, safety_tool.check_geofence
""",
        tools=["device_tool", "safety_tool"],
        capabilities=[
            AgentCapability.TOOL_USE,
            AgentCapability.NAVIGATION,
        ],
    ),
    "search_agent": AgentDefinition(
        name="search_agent",
        description="搜索任务专家，负责区域划分、搜索策略制定、目标识别",
        agent_type=AgentType.SPECIALIST,
        system_prompt="""你是搜索任务专家，负责规划和执行区域搜索任务。
你的能力包括：
- 将搜索区域划分为子区域
- 制定搜索策略（栅格搜索、螺旋搜索等）
- 分配搜索任务给多架无人机
- 处理目标发现和报告

可用工具：device_tool.goto, swarm_tool.assign_task
""",
        tools=["device_tool", "swarm_tool"],
        capabilities=[
            AgentCapability.TOOL_USE,
            AgentCapability.SEARCH,
            AgentCapability.PLANNING,
        ],
    ),
}


class AgentRegistry:
    """Agent 注册表"""
    
    def __init__(self):
        self._agents: Dict[str, AgentDefinition] = {}
        self._load_predefined()
    
    def _load_predefined(self) -> None:
        """加载预定义 Agent"""
        for name, definition in PREDEFINED_AGENTS.items():
            self._agents[name] = definition
    
    def register(self, definition: AgentDefinition) -> None:
        """注册 Agent"""
        self._agents[definition.name] = definition
        logger.info(f"[AgentRegistry] 注册 Agent: {definition.name}")
    
    def unregister(self, name: str) -> bool:
        """注销 Agent"""
        if name in self._agents:
            del self._agents[name]
            logger.info(f"[AgentRegistry] 注销 Agent: {name}")
            return True
        return False
    
    def get(self, name: str) -> Optional[AgentDefinition]:
        """获取 Agent 定义"""
        return self._agents.get(name)
    
    def list_agents(self) -> List[str]:
        """列出所有 Agent 名称"""
        return list(self._agents.keys())
    
    def list_by_type(self, agent_type: AgentType) -> List[AgentDefinition]:
        """按类型列出 Agent"""
        return [
            agent for agent in self._agents.values()
            if agent.agent_type == agent_type
        ]
    
    def list_by_capability(self, capability: AgentCapability) -> List[AgentDefinition]:
        """按能力列出 Agent"""
        return [
            agent for agent in self._agents.values()
            if capability in agent.capabilities
        ]
    
    def get_subagent_tools(self) -> List[ToolSchema]:
        """获取所有子代理作为工具的 Schema"""
        tools = []
        for agent in self._agents.values():
            if agent.agent_type == AgentType.SPECIALIST:
                tools.append(agent.to_tool_schema())
        return tools
    
    def to_dict(self) -> Dict[str, Dict[str, Any]]:
        """序列化为字典"""
        return {name: agent.to_dict() for name, agent in self._agents.items()}


# 全局注册表实例
_global_registry: Optional[AgentRegistry] = None


def get_agent_registry() -> AgentRegistry:
    """获取全局 Agent 注册表"""
    global _global_registry
    if _global_registry is None:
        _global_registry = AgentRegistry()
    return _global_registry


def register_agent(definition: AgentDefinition) -> None:
    """注册 Agent（便捷函数）"""
    get_agent_registry().register(definition)


def get_agent(name: str) -> Optional[AgentDefinition]:
    """获取 Agent（便捷函数）"""
    return get_agent_registry().get(name)

