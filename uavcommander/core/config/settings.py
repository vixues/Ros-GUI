"""
全局配置模块

定义系统的全局配置项和默认值。
"""

import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Environment(Enum):
    """运行环境"""
    
    DEVELOPMENT = "development"
    TESTING = "testing"
    SIMULATION = "simulation"
    PRODUCTION = "production"


class ApprovalMode(Enum):
    """审批模式"""
    
    STRICT = "strict"   # 所有操作需确认
    NORMAL = "normal"   # 仅危险操作需确认
    YOLO = "yolo"       # 自动批准所有（仅限仿真）


@dataclass
class SystemSettings:
    """系统设置"""
    
    # 环境配置
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = True
    log_level: str = "INFO"
    
    # 路径配置
    base_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent)
    log_dir: Path = field(default_factory=lambda: Path("logs"))
    data_dir: Path = field(default_factory=lambda: Path("data"))
    
    # 安全配置
    approval_mode: ApprovalMode = ApprovalMode.NORMAL
    max_concurrent_tools: int = 5
    tool_timeout_seconds: float = 60.0
    
    # Agent 配置
    max_turns: int = 50
    max_tool_calls_per_turn: int = 10
    enable_streaming: bool = True
    
    def __post_init__(self):
        # 确保目录存在
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def from_env(cls) -> "SystemSettings":
        """从环境变量创建配置"""
        env_str = os.getenv("UAV_ENVIRONMENT", "development")
        environment = Environment(env_str.lower())
        
        approval_str = os.getenv("UAV_APPROVAL_MODE", "normal")
        approval_mode = ApprovalMode(approval_str.lower())
        
        return cls(
            environment=environment,
            debug=os.getenv("UAV_DEBUG", "true").lower() == "true",
            log_level=os.getenv("UAV_LOG_LEVEL", "INFO"),
            approval_mode=approval_mode,
            max_concurrent_tools=int(os.getenv("UAV_MAX_CONCURRENT_TOOLS", "5")),
            tool_timeout_seconds=float(os.getenv("UAV_TOOL_TIMEOUT", "60.0")),
            max_turns=int(os.getenv("UAV_MAX_TURNS", "50")),
            enable_streaming=os.getenv("UAV_ENABLE_STREAMING", "true").lower() == "true",
        )


@dataclass
class Config:
    """统一配置类"""
    
    system: SystemSettings = field(default_factory=SystemSettings)
    llm_config: Optional[Dict[str, Any]] = None
    ros_config: Optional[Dict[str, Any]] = None
    safety_config: Optional[Dict[str, Any]] = None
    
    # 运行时配置
    _model: str = "gpt-4"
    _user_tier: Optional[str] = None
    
    def get_model(self) -> str:
        return self._model
    
    def set_model(self, model: str) -> None:
        self._model = model
    
    def get_approval_mode(self) -> ApprovalMode:
        return self.system.approval_mode
    
    def get_user_tier(self) -> Optional[str]:
        return self._user_tier
    
    def is_simulation(self) -> bool:
        return self.system.environment == Environment.SIMULATION
    
    def is_production(self) -> bool:
        return self.system.environment == Environment.PRODUCTION


# 全局配置实例
_global_config: Optional[Config] = None


def get_config() -> Config:
    """获取全局配置"""
    global _global_config
    if _global_config is None:
        _global_config = Config(system=SystemSettings.from_env())
    return _global_config


def set_config(config: Config) -> None:
    """设置全局配置"""
    global _global_config
    _global_config = config


def reset_config() -> None:
    """重置全局配置"""
    global _global_config
    _global_config = None

