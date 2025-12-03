"""
工具注册表模块

ToolRegistry - 管理工具的注册与发现。
"""

from typing import Optional, Dict, List, Any, Type
from dataclasses import dataclass, field
import logging

from core.schema import ToolSchema, ToolCallRequest
from .tools import DeclarativeTool, ToolInvocation, ToolCategory

logger = logging.getLogger(__name__)


@dataclass
class ToolRegistration:
    """工具注册信息"""
    
    tool: DeclarativeTool
    enabled: bool = True
    priority: int = 0
    server_name: Optional[str] = None  # MCP 服务器名称


class ToolRegistry:
    """
    工具注册表
    
    职责:
    - 工具注册与注销
    - 工具发现与查询
    - 按类别/服务器分组
    """
    
    def __init__(self):
        self._tools: Dict[str, ToolRegistration] = {}
        self._category_index: Dict[ToolCategory, List[str]] = {}
        self._server_index: Dict[str, List[str]] = {}
    
    def register(
        self,
        tool: DeclarativeTool,
        enabled: bool = True,
        priority: int = 0,
        server_name: Optional[str] = None,
    ) -> None:
        """注册工具"""
        registration = ToolRegistration(
            tool=tool,
            enabled=enabled,
            priority=priority,
            server_name=server_name,
        )
        
        self._tools[tool.name] = registration
        
        # 更新类别索引
        if tool.category not in self._category_index:
            self._category_index[tool.category] = []
        self._category_index[tool.category].append(tool.name)
        
        # 更新服务器索引
        if server_name:
            if server_name not in self._server_index:
                self._server_index[server_name] = []
            self._server_index[server_name].append(tool.name)
        
        logger.info(f"[ToolRegistry] 注册工具: {tool.name}")
    
    def unregister(self, name: str) -> bool:
        """注销工具"""
        if name not in self._tools:
            return False
        
        registration = self._tools.pop(name)
        tool = registration.tool
        
        # 更新索引
        if tool.category in self._category_index:
            self._category_index[tool.category].remove(name)
        
        if registration.server_name in self._server_index:
            self._server_index[registration.server_name].remove(name)
        
        logger.info(f"[ToolRegistry] 注销工具: {name}")
        return True
    
    def get(self, name: str) -> Optional[DeclarativeTool]:
        """获取工具"""
        registration = self._tools.get(name)
        if registration and registration.enabled:
            return registration.tool
        return None
    
    def get_by_full_name(self, full_name: str) -> Optional[DeclarativeTool]:
        """
        通过完整名称获取工具
        
        Args:
            full_name: 格式为 "tool_name.method_name" 或 "tool_name"
        """
        parts = full_name.split(".", 1)
        tool_name = parts[0]
        return self.get(tool_name)
    
    def list_tools(self, enabled_only: bool = True) -> List[DeclarativeTool]:
        """列出所有工具"""
        tools = []
        for registration in self._tools.values():
            if not enabled_only or registration.enabled:
                tools.append(registration.tool)
        return tools
    
    def list_by_category(self, category: ToolCategory) -> List[DeclarativeTool]:
        """按类别列出工具"""
        names = self._category_index.get(category, [])
        return [self._tools[n].tool for n in names if n in self._tools]
    
    def list_by_server(self, server_name: str) -> List[DeclarativeTool]:
        """按服务器列出工具"""
        names = self._server_index.get(server_name, [])
        return [self._tools[n].tool for n in names if n in self._tools]
    
    def get_all_schemas(self) -> List[ToolSchema]:
        """获取所有工具的 Schema"""
        schemas = []
        for tool in self.list_tools():
            schemas.extend(tool.get_schemas())
        return schemas
    
    def get_schemas_for_llm(self) -> List[Dict[str, Any]]:
        """获取 LLM 格式的工具定义"""
        return [schema.to_openai_format() for schema in self.get_all_schemas()]
    
    def build_invocation(
        self,
        request: ToolCallRequest,
    ) -> Optional[ToolInvocation]:
        """
        构建工具调用
        
        Args:
            request: 工具调用请求
        
        Returns:
            工具调用实例，未找到工具时返回 None
        """
        tool = self.get_by_full_name(request.name)
        if not tool:
            logger.warning(f"[ToolRegistry] 未找到工具: {request.name}")
            return None
        
        return ToolInvocation.from_request(request, tool)
    
    def enable(self, name: str) -> bool:
        """启用工具"""
        if name in self._tools:
            self._tools[name].enabled = True
            return True
        return False
    
    def disable(self, name: str) -> bool:
        """禁用工具"""
        if name in self._tools:
            self._tools[name].enabled = False
            return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "tools": {
                name: {
                    "enabled": reg.enabled,
                    "priority": reg.priority,
                    "server_name": reg.server_name,
                    "tool": reg.tool.to_dict(),
                }
                for name, reg in self._tools.items()
            },
            "categories": {
                cat.value: names
                for cat, names in self._category_index.items()
            },
            "servers": dict(self._server_index),
        }


# 全局注册表实例
_global_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """获取全局工具注册表"""
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry


def register_tool(
    tool: DeclarativeTool,
    enabled: bool = True,
    priority: int = 0,
) -> None:
    """注册工具（便捷函数）"""
    get_tool_registry().register(tool, enabled, priority)


def get_tool(name: str) -> Optional[DeclarativeTool]:
    """获取工具（便捷函数）"""
    return get_tool_registry().get(name)

