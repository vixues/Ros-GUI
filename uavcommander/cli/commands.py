"""
命令处理模块

定义 CLI 内置命令。
"""

from typing import Optional, Dict, List, Any, Callable, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum
import asyncio

from core.config import get_config
from core.tools import get_tool_registry
from core.agent import get_agent_registry

if TYPE_CHECKING:
    from .repl import REPL


@dataclass
class CommandResult:
    """命令执行结果"""
    
    success: bool
    output: Optional[str] = None
    data: Optional[Any] = None


class Command:
    """命令基类"""
    
    name: str = ""
    aliases: List[str] = []
    description: str = ""
    usage: str = ""
    
    async def execute(
        self,
        args: List[str],
        repl: Optional["REPL"] = None,
    ) -> CommandResult:
        """执行命令"""
        raise NotImplementedError


class HelpCommand(Command):
    """帮助命令"""
    
    name = "help"
    aliases = ["h", "?"]
    description = "显示帮助信息"
    usage = "help [command]"
    
    def __init__(self, handler: "CommandHandler"):
        self.handler = handler
    
    async def execute(
        self,
        args: List[str],
        repl: Optional["REPL"] = None,
    ) -> CommandResult:
        if args:
            # 显示特定命令帮助
            cmd_name = args[0]
            cmd = self.handler.get_command(cmd_name)
            if cmd:
                output = f"""
命令: {cmd.name}
别名: {', '.join(cmd.aliases) if cmd.aliases else '无'}
描述: {cmd.description}
用法: {cmd.usage}
"""
                return CommandResult(True, output.strip())
            else:
                return CommandResult(False, f"未知命令: {cmd_name}")
        
        # 显示所有命令
        lines = ["可用命令:", ""]
        
        for cmd in self.handler.list_commands():
            aliases = f" ({', '.join(cmd.aliases)})" if cmd.aliases else ""
            lines.append(f"  {cmd.name}{aliases}")
            lines.append(f"    {cmd.description}")
            lines.append("")
        
        lines.extend([
            "自然语言命令:",
            "  直接输入自然语言指令，例如:",
            "    - 让3架无人机起飞",
            "    - 建立V形编队飞往A点",
            "    - 查看所有无人机状态",
            "",
            "输入 'help <command>' 查看命令详情",
        ])
        
        return CommandResult(True, "\n".join(lines))


class ExitCommand(Command):
    """退出命令"""
    
    name = "exit"
    aliases = ["quit", "q"]
    description = "退出程序"
    usage = "exit"
    
    async def execute(
        self,
        args: List[str],
        repl: Optional["REPL"] = None,
    ) -> CommandResult:
        if repl:
            repl.exit()
        return CommandResult(True, "👋 再见！")


class StatusCommand(Command):
    """状态命令"""
    
    name = "status"
    aliases = ["st"]
    description = "显示系统状态"
    usage = "status"
    
    async def execute(
        self,
        args: List[str],
        repl: Optional["REPL"] = None,
    ) -> CommandResult:
        config = get_config()
        
        lines = [
            "系统状态:",
            f"  模型: {config.get_model()}",
            f"  审批模式: {config.get_approval_mode().value}",
            f"  仿真模式: {config.is_simulation()}",
            "",
        ]
        
        # 工具状态
        registry = get_tool_registry()
        tools = registry.list_tools()
        lines.append(f"已注册工具: {len(tools)}")
        for tool in tools:
            lines.append(f"  - {tool.name}: {tool.description[:40]}...")
        
        lines.append("")
        
        # Agent 状态
        agent_registry = get_agent_registry()
        agents = agent_registry.list_agents()
        lines.append(f"已注册代理: {len(agents)}")
        for name in agents:
            agent = agent_registry.get(name)
            if agent:
                lines.append(f"  - {name}: {agent.description[:40]}...")
        
        return CommandResult(True, "\n".join(lines))


class ToolsCommand(Command):
    """工具列表命令"""
    
    name = "tools"
    aliases = ["t"]
    description = "列出所有可用工具"
    usage = "tools [tool_name]"
    
    async def execute(
        self,
        args: List[str],
        repl: Optional["REPL"] = None,
    ) -> CommandResult:
        registry = get_tool_registry()
        
        if args:
            # 显示特定工具详情
            tool_name = args[0]
            tool = registry.get(tool_name)
            if not tool:
                return CommandResult(False, f"未找到工具: {tool_name}")
            
            lines = [
                f"工具: {tool.name}",
                f"描述: {tool.description}",
                f"类别: {tool.category.value}",
                "",
                "方法:",
            ]
            
            for method in tool.get_methods():
                dangerous = " ⚠️" if method.dangerous else ""
                lines.append(f"  - {method.name}{dangerous}")
                lines.append(f"    {method.description}")
                if method.required:
                    lines.append(f"    必需参数: {', '.join(method.required)}")
            
            return CommandResult(True, "\n".join(lines))
        
        # 列出所有工具
        tools = registry.list_tools()
        
        if not tools:
            return CommandResult(True, "没有已注册的工具")
        
        lines = ["可用工具:", ""]
        for tool in tools:
            lines.append(f"  {tool.name}")
            lines.append(f"    {tool.description}")
            lines.append(f"    方法: {', '.join(m.name for m in tool.get_methods())}")
            lines.append("")
        
        return CommandResult(True, "\n".join(lines))


class AgentsCommand(Command):
    """代理列表命令"""
    
    name = "agents"
    aliases = ["a"]
    description = "列出所有可用代理"
    usage = "agents [agent_name]"
    
    async def execute(
        self,
        args: List[str],
        repl: Optional["REPL"] = None,
    ) -> CommandResult:
        registry = get_agent_registry()
        
        if args:
            # 显示特定代理详情
            agent_name = args[0]
            agent = registry.get(agent_name)
            if not agent:
                return CommandResult(False, f"未找到代理: {agent_name}")
            
            lines = [
                f"代理: {agent.name}",
                f"描述: {agent.description}",
                f"类型: {agent.agent_type.value}",
                f"工具: {', '.join(agent.tools) if agent.tools else '无'}",
                f"能力: {', '.join(c.value for c in agent.capabilities) if agent.capabilities else '无'}",
            ]
            
            return CommandResult(True, "\n".join(lines))
        
        # 列出所有代理
        agents = registry.list_agents()
        
        if not agents:
            return CommandResult(True, "没有已注册的代理")
        
        lines = ["可用代理:", ""]
        for name in agents:
            agent = registry.get(name)
            if agent:
                lines.append(f"  {name} ({agent.agent_type.value})")
                lines.append(f"    {agent.description}")
                lines.append("")
        
        return CommandResult(True, "\n".join(lines))


class ClearCommand(Command):
    """清屏命令"""
    
    name = "clear"
    aliases = ["cls"]
    description = "清除屏幕"
    usage = "clear"
    
    async def execute(
        self,
        args: List[str],
        repl: Optional["REPL"] = None,
    ) -> CommandResult:
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
        return CommandResult(True, None)


class ModeCommand(Command):
    """模式切换命令"""
    
    name = "mode"
    aliases = ["m"]
    description = "切换审批模式"
    usage = "mode [strict|normal|yolo]"
    
    async def execute(
        self,
        args: List[str],
        repl: Optional["REPL"] = None,
    ) -> CommandResult:
        from core.config import ApprovalMode, get_config
        
        config = get_config()
        
        if not args:
            current = config.get_approval_mode()
            return CommandResult(True, f"当前审批模式: {current.value}")
        
        mode_str = args[0].lower()
        try:
            new_mode = ApprovalMode(mode_str)
            config.system.approval_mode = new_mode
            return CommandResult(True, f"审批模式已切换为: {new_mode.value}")
        except ValueError:
            return CommandResult(False, f"未知模式: {mode_str}，可选: strict/normal/yolo")


class CommandHandler:
    """命令处理器"""
    
    def __init__(self, repl: Optional["REPL"] = None):
        self.repl = repl
        self._commands: Dict[str, Command] = {}
        self._alias_map: Dict[str, str] = {}
        
        self._register_default_commands()
    
    def _register_default_commands(self) -> None:
        """注册默认命令"""
        commands = [
            HelpCommand(self),
            ExitCommand(),
            StatusCommand(),
            ToolsCommand(),
            AgentsCommand(),
            ClearCommand(),
            ModeCommand(),
        ]
        
        for cmd in commands:
            self.register(cmd)
    
    def register(self, command: Command) -> None:
        """注册命令"""
        self._commands[command.name] = command
        for alias in command.aliases:
            self._alias_map[alias] = command.name
    
    def get_command(self, name: str) -> Optional[Command]:
        """获取命令"""
        # 移除前导斜杠
        if name.startswith("/"):
            name = name[1:]
        
        # 检查别名
        if name in self._alias_map:
            name = self._alias_map[name]
        
        return self._commands.get(name)
    
    def list_commands(self) -> List[Command]:
        """列出所有命令"""
        return list(self._commands.values())
    
    async def handle(self, input_str: str) -> CommandResult:
        """处理命令输入"""
        # 解析命令和参数
        if input_str.startswith("/"):
            input_str = input_str[1:]
        
        parts = input_str.split()
        if not parts:
            return CommandResult(False, "空命令")
        
        cmd_name = parts[0].lower()
        args = parts[1:]
        
        # 查找命令
        command = self.get_command(cmd_name)
        if not command:
            return CommandResult(False, f"未知命令: {cmd_name}，输入 'help' 查看帮助")
        
        # 执行命令
        try:
            return await command.execute(args, self.repl)
        except Exception as e:
            return CommandResult(False, f"命令执行失败: {e}")

