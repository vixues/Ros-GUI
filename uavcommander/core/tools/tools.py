"""
声明式工具基类模块

DeclarativeTool - 定义工具的声明式接口。
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any, Callable, Awaitable, Union
from dataclasses import dataclass, field
from enum import Enum
import logging

from core.schema import ToolSchema, ToolResult, ToolCallRequest, ToolType

logger = logging.getLogger(__name__)


class ToolCategory(Enum):
    """工具类别"""
    
    DEVICE = "device"          # 单机控制
    SWARM = "swarm"            # 集群控制
    SAFETY = "safety"          # 安全控制
    NAVIGATION = "navigation"  # 导航
    SENSOR = "sensor"          # 传感器
    COMMUNICATION = "communication"  # 通信


@dataclass
class ToolMethod:
    """工具方法定义"""
    
    name: str
    description: str
    parameters: Dict[str, Any]
    required: List[str] = field(default_factory=list)
    dangerous: bool = False
    confirmation_required: bool = False
    returns: Optional[Dict[str, Any]] = None
    
    def to_schema(self, tool_name: str) -> ToolSchema:
        """转换为 ToolSchema"""
        full_name = f"{tool_name}.{self.name}"
        return ToolSchema(
            name=full_name,
            description=self.description,
            parameters=self.parameters,
            required=self.required,
            dangerous=self.dangerous,
            confirmation_required=self.confirmation_required,
            returns=self.returns,
        )


class DeclarativeTool(ABC):
    """
    声明式工具基类
    
    子类需要:
    1. 定义 name 和 description
    2. 定义 methods 列表
    3. 实现各方法的执行逻辑
    """
    
    # 工具名称
    name: str = "base_tool"
    
    # 工具描述
    description: str = "基础工具"
    
    # 工具类别
    category: ToolCategory = ToolCategory.DEVICE
    
    # 工具类型
    tool_type: ToolType = ToolType.NORMAL
    
    def __init__(self):
        self._methods: Dict[str, ToolMethod] = {}
        self._setup_methods()
    
    @abstractmethod
    def _setup_methods(self) -> None:
        """设置工具方法（子类实现）"""
        pass
    
    def register_method(self, method: ToolMethod) -> None:
        """注册方法"""
        self._methods[method.name] = method
    
    def get_methods(self) -> List[ToolMethod]:
        """获取所有方法"""
        return list(self._methods.values())
    
    def get_method(self, name: str) -> Optional[ToolMethod]:
        """获取指定方法"""
        return self._methods.get(name)
    
    def get_schemas(self) -> List[ToolSchema]:
        """获取所有方法的 Schema"""
        return [m.to_schema(self.name) for m in self._methods.values()]
    
    async def execute(
        self,
        method_name: str,
        args: Dict[str, Any],
    ) -> ToolResult:
        """
        执行工具方法
        
        Args:
            method_name: 方法名
            args: 参数
        
        Returns:
            执行结果
        """
        method = self._methods.get(method_name)
        if not method:
            return ToolResult.error_result(
                call_id="",
                error=f"未知方法: {method_name}",
            )
        
        # 验证必需参数
        for param in method.required:
            if param not in args:
                return ToolResult.error_result(
                    call_id="",
                    error=f"缺少必需参数: {param}",
                )
        
        try:
            # 调用实际方法
            handler = getattr(self, method_name, None)
            if handler is None:
                return ToolResult.error_result(
                    call_id="",
                    error=f"方法未实现: {method_name}",
                )
            
            result = await handler(**args)
            return result
            
        except Exception as e:
            logger.error(f"[{self.name}] 执行 {method_name} 失败: {e}")
            return ToolResult.error_result(
                call_id="",
                error=str(e),
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "tool_type": self.tool_type.value,
            "methods": [
                {
                    "name": m.name,
                    "description": m.description,
                    "parameters": m.parameters,
                    "required": m.required,
                    "dangerous": m.dangerous,
                }
                for m in self._methods.values()
            ],
        }


class ToolInvocation:
    """
    工具调用实例
    
    封装一次具体的工具调用。
    """
    
    def __init__(
        self,
        tool: DeclarativeTool,
        method_name: str,
        args: Dict[str, Any],
        call_id: str = "",
    ):
        self.tool = tool
        self.method_name = method_name
        self.args = args
        self.call_id = call_id
    
    @property
    def full_name(self) -> str:
        return f"{self.tool.name}.{self.method_name}"
    
    @property
    def method(self) -> Optional[ToolMethod]:
        return self.tool.get_method(self.method_name)
    
    @property
    def is_dangerous(self) -> bool:
        method = self.method
        return method.dangerous if method else False
    
    @property
    def requires_confirmation(self) -> bool:
        method = self.method
        if method:
            return method.dangerous or method.confirmation_required
        return False
    
    async def execute(self) -> ToolResult:
        """执行调用"""
        result = await self.tool.execute(self.method_name, self.args)
        result.call_id = self.call_id
        return result
    
    @classmethod
    def from_request(
        cls,
        request: ToolCallRequest,
        tool: DeclarativeTool,
    ) -> "ToolInvocation":
        """从请求创建调用"""
        # 解析方法名（格式: tool_name.method_name）
        parts = request.name.split(".", 1)
        method_name = parts[1] if len(parts) > 1 else parts[0]
        
        return cls(
            tool=tool,
            method_name=method_name,
            args=request.args,
            call_id=request.call_id,
        )


class CompositeResult:
    """组合结果（多个工具调用的结果）"""
    
    def __init__(self):
        self.results: List[ToolResult] = []
    
    def add(self, result: ToolResult) -> None:
        self.results.append(result)
    
    @property
    def all_success(self) -> bool:
        return all(r.success for r in self.results)
    
    @property
    def any_success(self) -> bool:
        return any(r.success for r in self.results)
    
    def to_tool_result(self, call_id: str = "") -> ToolResult:
        """合并为单个结果"""
        if not self.results:
            return ToolResult.error_result(call_id, "无结果")
        
        contents = []
        displays = []
        
        for r in self.results:
            if r.llm_content:
                for item in r.llm_content:
                    if isinstance(item, dict) and "text" in item:
                        contents.append(item["text"])
            if r.display_content:
                displays.append(r.display_content)
        
        return ToolResult(
            call_id=call_id,
            success=self.all_success,
            llm_content=[{"type": "text", "text": "\n".join(contents)}],
            display_content="\n".join(displays),
        )

