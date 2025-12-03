"""
ROS 参数配置模块

定义 ROS 2 通信相关的参数和配置。
"""

import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum


class ROSDistro(Enum):
    """ROS 发行版"""
    
    HUMBLE = "humble"
    IRON = "iron"
    JAZZY = "jazzy"


class QoSProfile(Enum):
    """QoS 配置"""
    
    DEFAULT = "default"
    SENSOR_DATA = "sensor_data"
    SERVICES = "services"
    PARAMETERS = "parameters"
    RELIABLE = "reliable"


@dataclass
class TopicConfig:
    """Topic 配置"""
    
    name: str
    msg_type: str
    qos: QoSProfile = QoSProfile.DEFAULT
    history_depth: int = 10
    
    def get_full_name(self, uav_id: Optional[str] = None) -> str:
        """获取完整 topic 名称"""
        if uav_id and "{uav_id}" in self.name:
            return self.name.format(uav_id=uav_id)
        return self.name


@dataclass
class ServiceConfig:
    """Service 配置"""
    
    name: str
    srv_type: str
    timeout: float = 10.0
    
    def get_full_name(self, uav_id: Optional[str] = None) -> str:
        """获取完整 service 名称"""
        if uav_id and "{uav_id}" in self.name:
            return self.name.format(uav_id=uav_id)
        return self.name


@dataclass
class ActionConfig:
    """Action 配置"""
    
    name: str
    action_type: str
    timeout: float = 60.0
    feedback_rate: float = 1.0  # Hz
    
    def get_full_name(self, uav_id: Optional[str] = None) -> str:
        """获取完整 action 名称"""
        if uav_id and "{uav_id}" in self.name:
            return self.name.format(uav_id=uav_id)
        return self.name


# 预定义 Topics
PREDEFINED_TOPICS: Dict[str, TopicConfig] = {
    "uav_pose": TopicConfig(
        name="/uav_{uav_id}/pose",
        msg_type="geometry_msgs/msg/PoseStamped",
        qos=QoSProfile.SENSOR_DATA,
    ),
    "uav_state": TopicConfig(
        name="/uav_{uav_id}/state",
        msg_type="mavros_msgs/msg/State",
        qos=QoSProfile.RELIABLE,
    ),
    "uav_battery": TopicConfig(
        name="/uav_{uav_id}/battery",
        msg_type="sensor_msgs/msg/BatteryState",
        qos=QoSProfile.SENSOR_DATA,
    ),
    "uav_velocity": TopicConfig(
        name="/uav_{uav_id}/velocity",
        msg_type="geometry_msgs/msg/TwistStamped",
        qos=QoSProfile.SENSOR_DATA,
    ),
    "swarm_status": TopicConfig(
        name="/swarm/status",
        msg_type="std_msgs/msg/String",
        qos=QoSProfile.RELIABLE,
    ),
}

# 预定义 Services
PREDEFINED_SERVICES: Dict[str, ServiceConfig] = {
    "arm": ServiceConfig(
        name="/uav_{uav_id}/arm",
        srv_type="mavros_msgs/srv/CommandBool",
        timeout=5.0,
    ),
    "set_mode": ServiceConfig(
        name="/uav_{uav_id}/set_mode",
        srv_type="mavros_msgs/srv/SetMode",
        timeout=5.0,
    ),
    "emergency_stop": ServiceConfig(
        name="/swarm/emergency_stop",
        srv_type="std_srvs/srv/Trigger",
        timeout=1.0,
    ),
}

# 预定义 Actions
PREDEFINED_ACTIONS: Dict[str, ActionConfig] = {
    "goto": ActionConfig(
        name="/uav_{uav_id}/goto",
        action_type="nav2_msgs/action/NavigateToPose",
        timeout=120.0,
    ),
    "takeoff": ActionConfig(
        name="/uav_{uav_id}/takeoff",
        action_type="uav_msgs/action/Takeoff",
        timeout=60.0,
    ),
    "land": ActionConfig(
        name="/uav_{uav_id}/land",
        action_type="uav_msgs/action/Land",
        timeout=60.0,
    ),
    "formation": ActionConfig(
        name="/swarm/formation",
        action_type="uav_msgs/action/Formation",
        timeout=180.0,
    ),
    "path_follow": ActionConfig(
        name="/uav_{uav_id}/path",
        action_type="nav2_msgs/action/FollowPath",
        timeout=300.0,
    ),
}


@dataclass
class ROSSettings:
    """ROS 设置"""
    
    # 基础配置
    distro: ROSDistro = ROSDistro.HUMBLE
    node_name: str = "uav_commander"
    namespace: str = ""
    
    # 域 ID (用于 DDS)
    domain_id: int = 0
    
    # 通信超时
    default_timeout: float = 10.0
    action_timeout: float = 60.0
    
    # QoS 配置
    default_qos_depth: int = 10
    
    # Topics/Services/Actions 配置
    topics: Dict[str, TopicConfig] = field(default_factory=lambda: PREDEFINED_TOPICS.copy())
    services: Dict[str, ServiceConfig] = field(default_factory=lambda: PREDEFINED_SERVICES.copy())
    actions: Dict[str, ActionConfig] = field(default_factory=lambda: PREDEFINED_ACTIONS.copy())
    
    # UAV 配置
    uav_id_prefix: str = "uav_"
    max_uav_count: int = 10
    
    # 仿真模式
    simulation_mode: bool = False
    gazebo_world: str = "empty.world"
    
    def get_topic(self, name: str) -> Optional[TopicConfig]:
        """获取 topic 配置"""
        return self.topics.get(name)
    
    def get_service(self, name: str) -> Optional[ServiceConfig]:
        """获取 service 配置"""
        return self.services.get(name)
    
    def get_action(self, name: str) -> Optional[ActionConfig]:
        """获取 action 配置"""
        return self.actions.get(name)
    
    def get_uav_ids(self, count: int) -> List[str]:
        """生成 UAV ID 列表"""
        return [f"{self.uav_id_prefix}{i+1}" for i in range(count)]
    
    @classmethod
    def from_env(cls) -> "ROSSettings":
        """从环境变量创建配置"""
        distro_str = os.getenv("ROS_DISTRO", "humble")
        try:
            distro = ROSDistro(distro_str.lower())
        except ValueError:
            distro = ROSDistro.HUMBLE
        
        return cls(
            distro=distro,
            node_name=os.getenv("UAV_NODE_NAME", "uav_commander"),
            namespace=os.getenv("UAV_NAMESPACE", ""),
            domain_id=int(os.getenv("ROS_DOMAIN_ID", "0")),
            simulation_mode=os.getenv("UAV_SIMULATION", "false").lower() == "true",
        )


@dataclass
class UAVConfig:
    """单个 UAV 配置"""
    
    uav_id: str
    name: str = ""
    type: str = "quadrotor"
    
    # 初始位置
    home_lat: float = 0.0
    home_lon: float = 0.0
    home_alt: float = 0.0
    
    # 能力
    max_speed: float = 15.0
    max_altitude: float = 120.0
    endurance_minutes: float = 30.0
    
    # 传感器
    has_camera: bool = True
    has_lidar: bool = False
    has_thermal: bool = False
    
    def __post_init__(self):
        if not self.name:
            self.name = self.uav_id


@dataclass
class SwarmConfig:
    """集群配置"""
    
    swarm_id: str = "default_swarm"
    uavs: List[UAVConfig] = field(default_factory=list)
    
    # 编队配置
    default_formation: str = "line"
    formation_spacing: float = 5.0
    
    # 同步配置
    sync_rate_hz: float = 10.0
    position_tolerance: float = 0.5
    
    def add_uav(self, uav: UAVConfig) -> None:
        """添加 UAV"""
        self.uavs.append(uav)
    
    def get_uav(self, uav_id: str) -> Optional[UAVConfig]:
        """获取 UAV 配置"""
        for uav in self.uavs:
            if uav.uav_id == uav_id:
                return uav
        return None
    
    def get_uav_ids(self) -> List[str]:
        """获取所有 UAV ID"""
        return [uav.uav_id for uav in self.uavs]

