"""
集群控制工具模块

SwarmTool - 控制无人机集群的协同操作。
"""

from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import math
import logging

from core.schema import ToolResult, ToolType
from .tools import DeclarativeTool, ToolMethod, ToolCategory

logger = logging.getLogger(__name__)


class FormationType(Enum):
    """编队类型"""
    
    LINE = "line"           # 线形
    V_SHAPE = "v_shape"     # V形
    CIRCLE = "circle"       # 圆形
    DIAMOND = "diamond"     # 菱形
    WEDGE = "wedge"         # 楔形
    GRID = "grid"           # 网格


@dataclass
class FormationSlot:
    """编队槽位"""
    
    slot_id: int
    uav_id: str
    offset_x: float  # 相对领航机的X偏移（米）
    offset_y: float  # 相对领航机的Y偏移（米）
    offset_z: float  # 相对领航机的Z偏移（米）


@dataclass
class SwarmState:
    """集群状态"""
    
    formation_type: Optional[FormationType] = None
    leader_id: Optional[str] = None
    slots: List[FormationSlot] = field(default_factory=list)
    target_lat: float = 0.0
    target_lon: float = 0.0
    target_alt: float = 0.0
    spacing: float = 10.0
    status: str = "idle"  # idle, forming, formed, moving, dispersing


class SwarmTool(DeclarativeTool):
    """
    集群控制工具
    
    提供无人机集群的协同控制操作。
    """
    
    name = "swarm_tool"
    description = "控制无人机集群的协同操作，包括编队、跟随、同步动作等"
    category = ToolCategory.SWARM
    tool_type = ToolType.MODIFICATION
    
    def __init__(self, device_tool: Optional[Any] = None):
        self.device_tool = device_tool
        self._swarm_state = SwarmState()
        super().__init__()
    
    def _setup_methods(self) -> None:
        """设置工具方法"""
        
        # form_formation - 建立编队
        self.register_method(ToolMethod(
            name="form_formation",
            description="让多架无人机建立指定的编队队形",
            parameters={
                "formation_type": {
                    "type": "string",
                    "description": "编队类型: line, v_shape, circle, diamond, wedge, grid",
                    "enum": ["line", "v_shape", "circle", "diamond", "wedge", "grid"],
                },
                "uav_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "参与编队的无人机ID列表",
                },
                "target_lat": {
                    "type": "number",
                    "description": "目标位置纬度",
                },
                "target_lon": {
                    "type": "number",
                    "description": "目标位置经度",
                },
                "target_alt": {
                    "type": "number",
                    "description": "目标高度（米）",
                },
                "spacing": {
                    "type": "number",
                    "description": "无人机间距（米）",
                    "default": 10.0,
                },
            },
            required=["formation_type", "uav_ids", "target_lat", "target_lon", "target_alt"],
            dangerous=True,
            confirmation_required=True,
        ))
        
        # disperse - 散开
        self.register_method(ToolMethod(
            name="disperse",
            description="散开当前编队",
            parameters={
                "uav_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "要散开的无人机ID列表",
                },
                "radius": {
                    "type": "number",
                    "description": "散开半径（米）",
                    "default": 50.0,
                },
            },
            required=["uav_ids"],
            dangerous=True,
        ))
        
        # follow_leader - 跟随领航机
        self.register_method(ToolMethod(
            name="follow_leader",
            description="让多架无人机跟随领航机飞行",
            parameters={
                "leader_id": {
                    "type": "string",
                    "description": "领航机ID",
                },
                "follower_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "跟随机ID列表",
                },
                "offset": {
                    "type": "number",
                    "description": "跟随距离（米）",
                    "default": 10.0,
                },
            },
            required=["leader_id", "follower_ids"],
            dangerous=True,
        ))
        
        # sync_action - 同步动作
        self.register_method(ToolMethod(
            name="sync_action",
            description="让多架无人机同步执行相同动作",
            parameters={
                "uav_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "无人机ID列表",
                },
                "action": {
                    "type": "string",
                    "description": "动作类型: takeoff, land, hover, rotate",
                    "enum": ["takeoff", "land", "hover", "rotate"],
                },
                "params": {
                    "type": "object",
                    "description": "动作参数",
                },
            },
            required=["uav_ids", "action"],
            dangerous=True,
        ))
        
        # assign_task - 分配任务
        self.register_method(ToolMethod(
            name="assign_task",
            description="为多架无人机分配任务",
            parameters={
                "uav_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "无人机ID列表",
                },
                "task_type": {
                    "type": "string",
                    "description": "任务类型: patrol, search, monitor",
                },
                "params": {
                    "type": "object",
                    "description": "任务参数",
                },
            },
            required=["uav_ids", "task_type"],
            dangerous=False,
        ))
        
        # get_swarm_status - 获取集群状态
        self.register_method(ToolMethod(
            name="get_swarm_status",
            description="获取当前集群状态",
            parameters={},
            required=[],
            dangerous=False,
        ))
    
    def _calculate_formation_slots(
        self,
        formation_type: FormationType,
        uav_ids: List[str],
        spacing: float,
    ) -> List[FormationSlot]:
        """计算编队槽位"""
        slots = []
        n = len(uav_ids)
        
        if formation_type == FormationType.LINE:
            # 线形编队
            for i, uav_id in enumerate(uav_ids):
                offset_y = (i - (n - 1) / 2) * spacing
                slots.append(FormationSlot(i, uav_id, 0, offset_y, 0))
        
        elif formation_type == FormationType.V_SHAPE:
            # V形编队
            angle = math.radians(60)  # V形角度
            for i, uav_id in enumerate(uav_ids):
                if i == 0:
                    slots.append(FormationSlot(0, uav_id, 0, 0, 0))
                else:
                    side = 1 if i % 2 == 1 else -1
                    row = (i + 1) // 2
                    offset_x = -row * spacing * math.cos(angle / 2)
                    offset_y = side * row * spacing * math.sin(angle / 2)
                    slots.append(FormationSlot(i, uav_id, offset_x, offset_y, 0))
        
        elif formation_type == FormationType.CIRCLE:
            # 圆形编队
            radius = spacing * n / (2 * math.pi) if n > 1 else 0
            for i, uav_id in enumerate(uav_ids):
                angle = 2 * math.pi * i / n
                offset_x = radius * math.cos(angle)
                offset_y = radius * math.sin(angle)
                slots.append(FormationSlot(i, uav_id, offset_x, offset_y, 0))
        
        elif formation_type == FormationType.DIAMOND:
            # 菱形编队
            positions = [(0, 0), (1, 1), (1, -1), (2, 0), (-1, 1), (-1, -1)]
            for i, uav_id in enumerate(uav_ids):
                if i < len(positions):
                    px, py = positions[i]
                else:
                    px, py = i, 0
                slots.append(FormationSlot(i, uav_id, px * spacing, py * spacing, 0))
        
        elif formation_type == FormationType.WEDGE:
            # 楔形编队
            for i, uav_id in enumerate(uav_ids):
                row = int((-1 + math.sqrt(1 + 8 * i)) / 2)
                pos_in_row = i - row * (row + 1) // 2
                offset_x = -row * spacing
                offset_y = (pos_in_row - row / 2) * spacing
                slots.append(FormationSlot(i, uav_id, offset_x, offset_y, 0))
        
        elif formation_type == FormationType.GRID:
            # 网格编队
            cols = int(math.ceil(math.sqrt(n)))
            for i, uav_id in enumerate(uav_ids):
                row = i // cols
                col = i % cols
                offset_x = (row - (n // cols) / 2) * spacing
                offset_y = (col - cols / 2) * spacing
                slots.append(FormationSlot(i, uav_id, offset_x, offset_y, 0))
        
        return slots
    
    async def form_formation(
        self,
        formation_type: str,
        uav_ids: List[str],
        target_lat: float,
        target_lon: float,
        target_alt: float,
        spacing: float = 10.0,
    ) -> ToolResult:
        """建立编队"""
        logger.info(f"[SwarmTool] 建立{formation_type}编队: {uav_ids}")
        
        if len(uav_ids) < 2:
            return ToolResult.error_result("", "编队至少需要2架无人机")
        
        try:
            ft = FormationType(formation_type)
        except ValueError:
            return ToolResult.error_result("", f"未知编队类型: {formation_type}")
        
        # 计算槽位
        slots = self._calculate_formation_slots(ft, uav_ids, spacing)
        
        # 更新状态
        self._swarm_state.formation_type = ft
        self._swarm_state.leader_id = uav_ids[0]
        self._swarm_state.slots = slots
        self._swarm_state.target_lat = target_lat
        self._swarm_state.target_lon = target_lon
        self._swarm_state.target_alt = target_alt
        self._swarm_state.spacing = spacing
        self._swarm_state.status = "forming"
        
        # 生成槽位分配信息
        slot_info = "\n".join([
            f"  - {s.uav_id}: 偏移 ({s.offset_x:.1f}, {s.offset_y:.1f}, {s.offset_z:.1f})m"
            for s in slots
        ])
        
        result_text = f"""编队指令已下发:
- 编队类型: {formation_type}
- 参与无人机: {len(uav_ids)} 架
- 目标位置: ({target_lat:.6f}, {target_lon:.6f}, {target_alt:.1f}m)
- 间距: {spacing}m
- 领航机: {uav_ids[0]}
- 槽位分配:
{slot_info}"""
        
        # 模拟完成
        self._swarm_state.status = "formed"
        
        return ToolResult.success_result(
            "",
            result_text,
            f"📐 {formation_type} 编队建立: {len(uav_ids)} 架无人机",
            metadata={
                "formation_type": formation_type,
                "uav_count": len(uav_ids),
                "leader": uav_ids[0],
                "slots": [{"uav_id": s.uav_id, "offset": [s.offset_x, s.offset_y, s.offset_z]} for s in slots],
            },
        )
    
    async def disperse(
        self,
        uav_ids: List[str],
        radius: float = 50.0,
    ) -> ToolResult:
        """散开编队"""
        logger.info(f"[SwarmTool] 散开: {uav_ids}, 半径 {radius}m")
        
        self._swarm_state.status = "dispersing"
        self._swarm_state.formation_type = None
        self._swarm_state.slots.clear()
        
        # 模拟完成
        self._swarm_state.status = "idle"
        
        return ToolResult.success_result(
            "",
            f"{len(uav_ids)} 架无人机正在散开，半径 {radius}m",
            f"💨 {len(uav_ids)} 架无人机散开",
            metadata={"uav_ids": uav_ids, "radius": radius},
        )
    
    async def follow_leader(
        self,
        leader_id: str,
        follower_ids: List[str],
        offset: float = 10.0,
    ) -> ToolResult:
        """跟随领航机"""
        logger.info(f"[SwarmTool] {follower_ids} 跟随 {leader_id}")
        
        self._swarm_state.leader_id = leader_id
        self._swarm_state.status = "following"
        
        return ToolResult.success_result(
            "",
            f"{len(follower_ids)} 架无人机开始跟随 {leader_id}，间距 {offset}m",
            f"👥 {len(follower_ids)} 架跟随 {leader_id}",
            metadata={
                "leader": leader_id,
                "followers": follower_ids,
                "offset": offset,
            },
        )
    
    async def sync_action(
        self,
        uav_ids: List[str],
        action: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> ToolResult:
        """同步动作"""
        params = params or {}
        logger.info(f"[SwarmTool] 同步动作 {action}: {uav_ids}")
        
        action_display = {
            "takeoff": "起飞",
            "land": "降落",
            "hover": "悬停",
            "rotate": "旋转",
        }.get(action, action)
        
        return ToolResult.success_result(
            "",
            f"{len(uav_ids)} 架无人机同步执行: {action_display}",
            f"🔄 同步{action_display}: {len(uav_ids)} 架",
            metadata={
                "uav_ids": uav_ids,
                "action": action,
                "params": params,
            },
        )
    
    async def assign_task(
        self,
        uav_ids: List[str],
        task_type: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> ToolResult:
        """分配任务"""
        params = params or {}
        logger.info(f"[SwarmTool] 分配任务 {task_type}: {uav_ids}")
        
        task_display = {
            "patrol": "巡逻",
            "search": "搜索",
            "monitor": "监控",
        }.get(task_type, task_type)
        
        return ToolResult.success_result(
            "",
            f"已为 {len(uav_ids)} 架无人机分配{task_display}任务",
            f"📋 {task_display}任务: {len(uav_ids)} 架",
            metadata={
                "uav_ids": uav_ids,
                "task_type": task_type,
                "params": params,
            },
        )
    
    async def get_swarm_status(self) -> ToolResult:
        """获取集群状态"""
        state = self._swarm_state
        
        if state.formation_type:
            status_text = f"""集群状态:
- 编队类型: {state.formation_type.value}
- 领航机: {state.leader_id}
- 成员数: {len(state.slots)}
- 间距: {state.spacing}m
- 状态: {state.status}
- 目标: ({state.target_lat:.6f}, {state.target_lon:.6f}, {state.target_alt:.1f}m)"""
        else:
            status_text = f"集群状态: {state.status}，无活动编队"
        
        return ToolResult.success_result(
            "",
            status_text,
            f"🔷 集群: {state.status}",
            metadata={
                "formation_type": state.formation_type.value if state.formation_type else None,
                "leader_id": state.leader_id,
                "member_count": len(state.slots),
                "status": state.status,
            },
        )

