"""
安全策略配置模块

定义无人机操作的安全策略和限制。
"""

from typing import Optional, Dict, Any, List, Set
from dataclasses import dataclass, field
from enum import Enum


class RiskLevel(Enum):
    """风险等级"""
    
    LOW = "low"         # 低风险 - 仅 STRICT 模式确认
    MEDIUM = "medium"   # 中风险 - NORMAL 模式需确认
    HIGH = "high"       # 高风险 - 必须确认
    CRITICAL = "critical"  # 危急 - 需要多重确认


class SafetyAction(Enum):
    """安全动作"""
    
    ALLOW = "allow"           # 允许执行
    CONFIRM = "confirm"       # 需要确认
    DENY = "deny"             # 拒绝执行
    EMERGENCY = "emergency"   # 紧急处理


@dataclass
class GeofenceZone:
    """地理围栏区域"""
    
    name: str
    zone_type: str  # no_fly, restricted, caution
    # 边界定义 (简化为矩形)
    min_lat: float = 0.0
    max_lat: float = 0.0
    min_lon: float = 0.0
    max_lon: float = 0.0
    min_alt: float = 0.0
    max_alt: float = float('inf')
    # 是否活跃
    active: bool = True
    
    def contains(self, lat: float, lon: float, alt: float = 0.0) -> bool:
        """检查点是否在区域内"""
        return (
            self.min_lat <= lat <= self.max_lat and
            self.min_lon <= lon <= self.max_lon and
            self.min_alt <= alt <= self.max_alt
        )


@dataclass
class OperationLimits:
    """操作限制"""
    
    # 高度限制 (米)
    min_altitude: float = 0.0
    max_altitude: float = 120.0
    
    # 速度限制 (米/秒)
    max_horizontal_speed: float = 15.0
    max_vertical_speed: float = 5.0
    
    # 加速度限制 (米/秒²)
    max_acceleration: float = 3.0
    
    # 距离限制 (米)
    max_distance_from_home: float = 5000.0
    min_distance_between_uavs: float = 5.0
    
    # 电池限制 (%)
    min_battery_level: float = 20.0
    critical_battery_level: float = 10.0
    
    # 风速限制 (米/秒)
    max_wind_speed: float = 10.0
    
    # 时间限制 (秒)
    max_flight_time: float = 1800.0  # 30分钟
    
    def validate_altitude(self, altitude: float) -> tuple[bool, str]:
        """验证高度"""
        if altitude < self.min_altitude:
            return False, f"高度 {altitude}m 低于最低限制 {self.min_altitude}m"
        if altitude > self.max_altitude:
            return False, f"高度 {altitude}m 超过最高限制 {self.max_altitude}m"
        return True, ""
    
    def validate_speed(self, h_speed: float, v_speed: float) -> tuple[bool, str]:
        """验证速度"""
        if h_speed > self.max_horizontal_speed:
            return False, f"水平速度 {h_speed}m/s 超过限制 {self.max_horizontal_speed}m/s"
        if v_speed > self.max_vertical_speed:
            return False, f"垂直速度 {v_speed}m/s 超过限制 {self.max_vertical_speed}m/s"
        return True, ""
    
    def validate_battery(self, level: float) -> tuple[bool, str]:
        """验证电量"""
        if level <= self.critical_battery_level:
            return False, f"电量 {level}% 已达危急水平，必须立即降落"
        if level <= self.min_battery_level:
            return False, f"电量 {level}% 过低，建议返航"
        return True, ""


# 危险操作分类
DANGEROUS_OPERATIONS: Dict[RiskLevel, List[str]] = {
    RiskLevel.HIGH: [
        "device_tool.arm",
        "device_tool.takeoff",
        "swarm_tool.form_formation",
        "swarm_tool.disperse",
    ],
    RiskLevel.MEDIUM: [
        "device_tool.goto",
        "device_tool.set_velocity",
        "swarm_tool.sync_action",
        "swarm_tool.follow_leader",
    ],
    RiskLevel.LOW: [
        "device_tool.get_status",
        "device_tool.land",
        "device_tool.get_position",
    ],
}


@dataclass
class SafetyPolicy:
    """安全策略配置"""
    
    # 操作限制
    limits: OperationLimits = field(default_factory=OperationLimits)
    
    # 地理围栏
    geofences: List[GeofenceZone] = field(default_factory=list)
    
    # 需要确认的操作
    confirmation_required: Set[str] = field(default_factory=set)
    
    # 始终允许的操作（不需要确认）
    always_allowed: Set[str] = field(default_factory=lambda: {
        "device_tool.get_status",
        "device_tool.get_position",
        "device_tool.get_battery",
    })
    
    # 始终拒绝的操作
    always_denied: Set[str] = field(default_factory=set)
    
    # 紧急停止触发条件
    emergency_stop_triggers: List[str] = field(default_factory=lambda: [
        "collision_imminent",
        "geofence_breach",
        "critical_battery",
        "communication_lost",
    ])
    
    def __post_init__(self):
        # 根据危险操作分类初始化确认列表
        for risk_level, operations in DANGEROUS_OPERATIONS.items():
            if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                self.confirmation_required.update(operations)
    
    def get_risk_level(self, operation: str) -> RiskLevel:
        """获取操作的风险等级"""
        for level, operations in DANGEROUS_OPERATIONS.items():
            if operation in operations:
                return level
        return RiskLevel.LOW
    
    def requires_confirmation(self, operation: str, approval_mode: str) -> bool:
        """检查操作是否需要确认"""
        if operation in self.always_allowed:
            return False
        if operation in self.always_denied:
            return True  # 将被拒绝，但仍需用户知晓
        
        risk_level = self.get_risk_level(operation)
        
        if approval_mode == "yolo":
            return False
        elif approval_mode == "strict":
            return True
        else:  # normal
            return risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL, RiskLevel.MEDIUM]
    
    def check_geofence(self, lat: float, lon: float, alt: float) -> tuple[bool, Optional[str]]:
        """检查地理围栏"""
        for zone in self.geofences:
            if zone.active and zone.contains(lat, lon, alt):
                if zone.zone_type == "no_fly":
                    return False, f"位置在禁飞区 '{zone.name}' 内"
                elif zone.zone_type == "restricted":
                    return False, f"位置在限制区 '{zone.name}' 内，需要特殊许可"
        return True, None
    
    def validate_operation(
        self,
        operation: str,
        params: Dict[str, Any],
    ) -> tuple[SafetyAction, str]:
        """验证操作安全性"""
        # 检查是否被拒绝
        if operation in self.always_denied:
            return SafetyAction.DENY, f"操作 '{operation}' 被策略禁止"
        
        # 检查位置参数
        if "lat" in params and "lon" in params:
            alt = params.get("alt", params.get("altitude", 0))
            ok, msg = self.check_geofence(params["lat"], params["lon"], alt)
            if not ok:
                return SafetyAction.DENY, msg
        
        # 检查高度
        if "altitude" in params:
            ok, msg = self.limits.validate_altitude(params["altitude"])
            if not ok:
                return SafetyAction.DENY, msg
        
        # 检查速度
        if "speed" in params or "velocity" in params:
            speed = params.get("speed", 0) or params.get("velocity", 0)
            ok, msg = self.limits.validate_speed(speed, 0)
            if not ok:
                return SafetyAction.DENY, msg
        
        # 确定是否需要确认
        if operation in self.confirmation_required:
            return SafetyAction.CONFIRM, f"操作 '{operation}' 需要确认"
        
        return SafetyAction.ALLOW, ""


# 默认安全策略实例
_default_policy: Optional[SafetyPolicy] = None


def get_safety_policy() -> SafetyPolicy:
    """获取默认安全策略"""
    global _default_policy
    if _default_policy is None:
        _default_policy = SafetyPolicy()
    return _default_policy


def set_safety_policy(policy: SafetyPolicy) -> None:
    """设置默认安全策略"""
    global _default_policy
    _default_policy = policy

