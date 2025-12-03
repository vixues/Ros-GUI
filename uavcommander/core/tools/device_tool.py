"""
单机控制工具模块

DeviceTool - 控制单架无人机的基本操作。
"""

from typing import Optional, Dict, List, Any
from dataclasses import dataclass
import asyncio
import logging

from core.schema import ToolResult, ToolType
from core.config import get_safety_policy, SafetyAction
from .tools import DeclarativeTool, ToolMethod, ToolCategory

logger = logging.getLogger(__name__)


@dataclass
class UAVState:
    """无人机状态"""
    
    uav_id: str
    armed: bool = False
    mode: str = "MANUAL"
    connected: bool = True
    
    # 位置
    latitude: float = 0.0
    longitude: float = 0.0
    altitude: float = 0.0
    
    # 速度
    vx: float = 0.0
    vy: float = 0.0
    vz: float = 0.0
    
    # 姿态
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0
    
    # 电池
    battery_percent: float = 100.0
    battery_voltage: float = 12.6
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "uav_id": self.uav_id,
            "armed": self.armed,
            "mode": self.mode,
            "connected": self.connected,
            "position": {
                "lat": self.latitude,
                "lon": self.longitude,
                "alt": self.altitude,
            },
            "velocity": {
                "vx": self.vx,
                "vy": self.vy,
                "vz": self.vz,
            },
            "attitude": {
                "roll": self.roll,
                "pitch": self.pitch,
                "yaw": self.yaw,
            },
            "battery": {
                "percent": self.battery_percent,
                "voltage": self.battery_voltage,
            },
        }


class DeviceTool(DeclarativeTool):
    """
    单机控制工具
    
    提供单架无人机的基本控制操作。
    """
    
    name = "device_tool"
    description = "控制单架无人机的基本操作，包括起飞、降落、飞行等"
    category = ToolCategory.DEVICE
    tool_type = ToolType.MODIFICATION
    
    def __init__(self, ros_bridge: Optional[Any] = None):
        self.ros_bridge = ros_bridge
        self._state_cache: Dict[str, UAVState] = {}
        super().__init__()
    
    def _setup_methods(self) -> None:
        """设置工具方法"""
        
        # arm - 解锁
        self.register_method(ToolMethod(
            name="arm",
            description="解锁无人机电机，准备起飞",
            parameters={
                "uav_id": {
                    "type": "string",
                    "description": "无人机ID",
                },
            },
            required=["uav_id"],
            dangerous=True,
            confirmation_required=True,
        ))
        
        # disarm - 锁定
        self.register_method(ToolMethod(
            name="disarm",
            description="锁定无人机电机",
            parameters={
                "uav_id": {
                    "type": "string",
                    "description": "无人机ID",
                },
            },
            required=["uav_id"],
            dangerous=False,
        ))
        
        # takeoff - 起飞
        self.register_method(ToolMethod(
            name="takeoff",
            description="起飞到指定高度",
            parameters={
                "uav_id": {
                    "type": "string",
                    "description": "无人机ID",
                },
                "altitude": {
                    "type": "number",
                    "description": "目标高度（米）",
                    "minimum": 1,
                    "maximum": 120,
                },
            },
            required=["uav_id", "altitude"],
            dangerous=True,
            confirmation_required=True,
        ))
        
        # land - 降落
        self.register_method(ToolMethod(
            name="land",
            description="降落到地面",
            parameters={
                "uav_id": {
                    "type": "string",
                    "description": "无人机ID",
                },
            },
            required=["uav_id"],
            dangerous=False,
        ))
        
        # goto - 飞往指定位置
        self.register_method(ToolMethod(
            name="goto",
            description="飞往指定GPS坐标",
            parameters={
                "uav_id": {
                    "type": "string",
                    "description": "无人机ID",
                },
                "lat": {
                    "type": "number",
                    "description": "目标纬度",
                },
                "lon": {
                    "type": "number",
                    "description": "目标经度",
                },
                "alt": {
                    "type": "number",
                    "description": "目标高度（米）",
                },
                "speed": {
                    "type": "number",
                    "description": "飞行速度（米/秒）",
                    "default": 5.0,
                },
            },
            required=["uav_id", "lat", "lon", "alt"],
            dangerous=True,
        ))
        
        # set_velocity - 设置速度
        self.register_method(ToolMethod(
            name="set_velocity",
            description="设置无人机速度",
            parameters={
                "uav_id": {
                    "type": "string",
                    "description": "无人机ID",
                },
                "vx": {
                    "type": "number",
                    "description": "X方向速度（米/秒）",
                },
                "vy": {
                    "type": "number",
                    "description": "Y方向速度（米/秒）",
                },
                "vz": {
                    "type": "number",
                    "description": "Z方向速度（米/秒）",
                },
            },
            required=["uav_id", "vx", "vy", "vz"],
            dangerous=True,
        ))
        
        # get_status - 获取状态
        self.register_method(ToolMethod(
            name="get_status",
            description="获取无人机当前状态",
            parameters={
                "uav_id": {
                    "type": "string",
                    "description": "无人机ID",
                },
            },
            required=["uav_id"],
            dangerous=False,
        ))
        
        # get_position - 获取位置
        self.register_method(ToolMethod(
            name="get_position",
            description="获取无人机当前位置",
            parameters={
                "uav_id": {
                    "type": "string",
                    "description": "无人机ID",
                },
            },
            required=["uav_id"],
            dangerous=False,
        ))
        
        # get_battery - 获取电量
        self.register_method(ToolMethod(
            name="get_battery",
            description="获取无人机电池状态",
            parameters={
                "uav_id": {
                    "type": "string",
                    "description": "无人机ID",
                },
            },
            required=["uav_id"],
            dangerous=False,
        ))
    
    def _get_state(self, uav_id: str) -> UAVState:
        """获取或创建无人机状态"""
        if uav_id not in self._state_cache:
            self._state_cache[uav_id] = UAVState(uav_id=uav_id)
        return self._state_cache[uav_id]
    
    async def arm(self, uav_id: str) -> ToolResult:
        """解锁无人机"""
        logger.info(f"[DeviceTool] 解锁 {uav_id}")
        
        state = self._get_state(uav_id)
        
        if not state.connected:
            return ToolResult.error_result("", f"无人机 {uav_id} 未连接")
        
        if state.armed:
            return ToolResult.success_result(
                "",
                f"无人机 {uav_id} 已经解锁",
                f"ℹ️ {uav_id} 已解锁"
            )
        
        # 模拟 ROS 调用
        if self.ros_bridge:
            # await self.ros_bridge.call_arm(uav_id, True)
            pass
        
        state.armed = True
        
        return ToolResult.success_result(
            "",
            f"无人机 {uav_id} 解锁成功",
            f"✅ {uav_id} 已解锁",
        )
    
    async def disarm(self, uav_id: str) -> ToolResult:
        """锁定无人机"""
        logger.info(f"[DeviceTool] 锁定 {uav_id}")
        
        state = self._get_state(uav_id)
        
        if not state.armed:
            return ToolResult.success_result(
                "",
                f"无人机 {uav_id} 已经锁定",
                f"ℹ️ {uav_id} 已锁定"
            )
        
        state.armed = False
        
        return ToolResult.success_result(
            "",
            f"无人机 {uav_id} 锁定成功",
            f"✅ {uav_id} 已锁定",
        )
    
    async def takeoff(self, uav_id: str, altitude: float) -> ToolResult:
        """起飞"""
        logger.info(f"[DeviceTool] {uav_id} 起飞到 {altitude}m")
        
        state = self._get_state(uav_id)
        
        # 检查状态
        if not state.connected:
            return ToolResult.error_result("", f"无人机 {uav_id} 未连接")
        
        if not state.armed:
            return ToolResult.error_result("", f"无人机 {uav_id} 未解锁，请先解锁")
        
        if state.altitude > 0.5:
            return ToolResult.error_result("", f"无人机 {uav_id} 已在空中")
        
        # 验证高度
        policy = get_safety_policy()
        ok, msg = policy.limits.validate_altitude(altitude)
        if not ok:
            return ToolResult.error_result("", msg)
        
        # 模拟起飞
        state.altitude = altitude
        state.mode = "GUIDED"
        
        return ToolResult.success_result(
            "",
            f"无人机 {uav_id} 正在起飞到 {altitude}m",
            f"🚀 {uav_id} 起飞中 → {altitude}m",
            metadata={"target_altitude": altitude},
        )
    
    async def land(self, uav_id: str) -> ToolResult:
        """降落"""
        logger.info(f"[DeviceTool] {uav_id} 降落")
        
        state = self._get_state(uav_id)
        
        if state.altitude < 0.5:
            return ToolResult.success_result(
                "",
                f"无人机 {uav_id} 已在地面",
                f"ℹ️ {uav_id} 已着陆"
            )
        
        # 模拟降落
        state.altitude = 0
        state.mode = "LAND"
        state.armed = False
        
        return ToolResult.success_result(
            "",
            f"无人机 {uav_id} 正在降落",
            f"🛬 {uav_id} 降落中",
        )
    
    async def goto(
        self,
        uav_id: str,
        lat: float,
        lon: float,
        alt: float,
        speed: float = 5.0,
    ) -> ToolResult:
        """飞往指定位置"""
        logger.info(f"[DeviceTool] {uav_id} 飞往 ({lat}, {lon}, {alt})")
        
        state = self._get_state(uav_id)
        
        if not state.armed:
            return ToolResult.error_result("", f"无人机 {uav_id} 未解锁")
        
        if state.altitude < 0.5:
            return ToolResult.error_result("", f"无人机 {uav_id} 未起飞")
        
        # 验证目标位置
        policy = get_safety_policy()
        ok, msg = policy.check_geofence(lat, lon, alt)
        if not ok:
            return ToolResult.error_result("", msg)
        
        # 模拟飞行
        state.latitude = lat
        state.longitude = lon
        state.altitude = alt
        state.mode = "GUIDED"
        
        return ToolResult.success_result(
            "",
            f"无人机 {uav_id} 正在飞往目标位置 ({lat:.6f}, {lon:.6f}, {alt}m)，速度 {speed}m/s",
            f"✈️ {uav_id} → ({lat:.4f}, {lon:.4f}, {alt}m)",
            metadata={
                "target": {"lat": lat, "lon": lon, "alt": alt},
                "speed": speed,
            },
        )
    
    async def set_velocity(
        self,
        uav_id: str,
        vx: float,
        vy: float,
        vz: float,
    ) -> ToolResult:
        """设置速度"""
        logger.info(f"[DeviceTool] {uav_id} 设置速度 ({vx}, {vy}, {vz})")
        
        state = self._get_state(uav_id)
        
        if not state.armed:
            return ToolResult.error_result("", f"无人机 {uav_id} 未解锁")
        
        # 验证速度
        policy = get_safety_policy()
        h_speed = (vx ** 2 + vy ** 2) ** 0.5
        ok, msg = policy.limits.validate_speed(h_speed, abs(vz))
        if not ok:
            return ToolResult.error_result("", msg)
        
        state.vx = vx
        state.vy = vy
        state.vz = vz
        
        return ToolResult.success_result(
            "",
            f"无人机 {uav_id} 速度已设置为 ({vx}, {vy}, {vz}) m/s",
            f"⚡ {uav_id} 速度: ({vx:.1f}, {vy:.1f}, {vz:.1f})",
        )
    
    async def get_status(self, uav_id: str) -> ToolResult:
        """获取状态"""
        state = self._get_state(uav_id)
        
        status_text = f"""无人机 {uav_id} 状态:
- 连接: {'已连接' if state.connected else '未连接'}
- 解锁: {'已解锁' if state.armed else '已锁定'}
- 模式: {state.mode}
- 位置: ({state.latitude:.6f}, {state.longitude:.6f}, {state.altitude:.1f}m)
- 电量: {state.battery_percent:.0f}%"""
        
        return ToolResult.success_result(
            "",
            status_text,
            f"📊 {uav_id}: {'🟢' if state.connected else '🔴'} {state.mode} {state.battery_percent:.0f}%",
            metadata=state.to_dict(),
        )
    
    async def get_position(self, uav_id: str) -> ToolResult:
        """获取位置"""
        state = self._get_state(uav_id)
        
        position_text = f"无人机 {uav_id} 位置: ({state.latitude:.6f}, {state.longitude:.6f}, {state.altitude:.1f}m)"
        
        return ToolResult.success_result(
            "",
            position_text,
            f"📍 {uav_id}: ({state.latitude:.4f}, {state.longitude:.4f}, {state.altitude:.1f}m)",
            metadata={
                "lat": state.latitude,
                "lon": state.longitude,
                "alt": state.altitude,
            },
        )
    
    async def get_battery(self, uav_id: str) -> ToolResult:
        """获取电量"""
        state = self._get_state(uav_id)
        
        # 电量警告
        warning = ""
        if state.battery_percent <= 10:
            warning = " ⚠️ 电量危急！"
        elif state.battery_percent <= 20:
            warning = " ⚠️ 电量低，建议返航"
        
        battery_text = f"无人机 {uav_id} 电池: {state.battery_percent:.0f}% ({state.battery_voltage:.2f}V){warning}"
        
        return ToolResult.success_result(
            "",
            battery_text,
            f"🔋 {uav_id}: {state.battery_percent:.0f}%{warning}",
            metadata={
                "percent": state.battery_percent,
                "voltage": state.battery_voltage,
            },
        )

