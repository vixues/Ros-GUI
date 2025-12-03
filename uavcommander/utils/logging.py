"""
日志系统模块

提供统一的日志配置和输出功能。
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from enum import Enum
import json


class LogLevel(Enum):
    """日志级别"""
    
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class LogFormat(Enum):
    """日志格式"""
    
    SIMPLE = "simple"
    DETAILED = "detailed"
    JSON = "json"


# 格式化字符串
LOG_FORMATS = {
    LogFormat.SIMPLE: "%(asctime)s - %(levelname)s - %(message)s",
    LogFormat.DETAILED: "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    LogFormat.JSON: None,  # 使用自定义 formatter
}


class JSONFormatter(logging.Formatter):
    """JSON 格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # 添加额外字段
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data
        
        return json.dumps(log_data, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器（用于终端输出）"""
    
    COLORS = {
        logging.DEBUG: "\033[36m",     # Cyan
        logging.INFO: "\033[32m",      # Green
        logging.WARNING: "\033[33m",   # Yellow
        logging.ERROR: "\033[31m",     # Red
        logging.CRITICAL: "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    
    def __init__(self, fmt: str, use_colors: bool = True):
        super().__init__(fmt)
        self.use_colors = use_colors
    
    def format(self, record: logging.LogRecord) -> str:
        if self.use_colors and sys.stdout.isatty():
            color = self.COLORS.get(record.levelno, "")
            record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


@dataclass
class LogConfig:
    """日志配置"""
    
    level: LogLevel = LogLevel.INFO
    format: LogFormat = LogFormat.DETAILED
    
    # 控制台输出
    console_enabled: bool = True
    console_colors: bool = True
    
    # 文件输出
    file_enabled: bool = True
    file_path: Path = Path("logs/uav_commander.log")
    file_max_size: int = 10 * 1024 * 1024  # 10MB
    file_backup_count: int = 5
    
    # 按时间轮转
    time_rotation: bool = False
    rotation_when: str = "midnight"
    rotation_interval: int = 1
    
    # JSON 日志文件（用于分析）
    json_file_enabled: bool = False
    json_file_path: Path = Path("logs/uav_commander.jsonl")


class LoggerManager:
    """日志管理器"""
    
    _instance: Optional["LoggerManager"] = None
    _initialized: bool = False
    
    def __new__(cls) -> "LoggerManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.config = LogConfig()
        self.loggers: Dict[str, logging.Logger] = {}
        self._root_logger: Optional[logging.Logger] = None
        LoggerManager._initialized = True
    
    def setup(self, config: Optional[LogConfig] = None) -> None:
        """设置日志系统"""
        if config:
            self.config = config
        
        # 确保日志目录存在
        if self.config.file_enabled:
            self.config.file_path.parent.mkdir(parents=True, exist_ok=True)
        if self.config.json_file_enabled:
            self.config.json_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 配置根日志器
        root_logger = logging.getLogger("uav_commander")
        root_logger.setLevel(self.config.level.value)
        root_logger.handlers.clear()
        
        # 控制台处理器
        if self.config.console_enabled:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.config.level.value)
            
            if self.config.format == LogFormat.JSON:
                console_handler.setFormatter(JSONFormatter())
            else:
                fmt = LOG_FORMATS[self.config.format]
                formatter = ColoredFormatter(fmt, self.config.console_colors)
                console_handler.setFormatter(formatter)
            
            root_logger.addHandler(console_handler)
        
        # 文件处理器
        if self.config.file_enabled:
            if self.config.time_rotation:
                file_handler = TimedRotatingFileHandler(
                    str(self.config.file_path),
                    when=self.config.rotation_when,
                    interval=self.config.rotation_interval,
                    backupCount=self.config.file_backup_count,
                    encoding="utf-8",
                )
            else:
                file_handler = RotatingFileHandler(
                    str(self.config.file_path),
                    maxBytes=self.config.file_max_size,
                    backupCount=self.config.file_backup_count,
                    encoding="utf-8",
                )
            
            file_handler.setLevel(self.config.level.value)
            fmt = LOG_FORMATS[LogFormat.DETAILED]
            file_handler.setFormatter(logging.Formatter(fmt))
            root_logger.addHandler(file_handler)
        
        # JSON 文件处理器
        if self.config.json_file_enabled:
            json_handler = RotatingFileHandler(
                str(self.config.json_file_path),
                maxBytes=self.config.file_max_size,
                backupCount=self.config.file_backup_count,
                encoding="utf-8",
            )
            json_handler.setLevel(self.config.level.value)
            json_handler.setFormatter(JSONFormatter())
            root_logger.addHandler(json_handler)
        
        self._root_logger = root_logger
    
    def get_logger(self, name: str) -> logging.Logger:
        """获取日志器"""
        if name in self.loggers:
            return self.loggers[name]
        
        logger = logging.getLogger(f"uav_commander.{name}")
        self.loggers[name] = logger
        return logger


# 全局日志管理器实例
_manager = LoggerManager()


def setup_logging(config: Optional[LogConfig] = None) -> None:
    """设置日志系统"""
    _manager.setup(config)


def get_logger(name: str = "main") -> logging.Logger:
    """获取日志器"""
    if not _manager._initialized or _manager._root_logger is None:
        _manager.setup()
    return _manager.get_logger(name)


class TaskLogger:
    """任务日志器 - 为特定任务添加上下文"""
    
    def __init__(self, task_id: str, logger: Optional[logging.Logger] = None):
        self.task_id = task_id
        self.logger = logger or get_logger("task")
    
    def _format_message(self, message: str) -> str:
        return f"[Task {self.task_id}] {message}"
    
    def debug(self, message: str, **kwargs) -> None:
        self.logger.debug(self._format_message(message), **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        self.logger.info(self._format_message(message), **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        self.logger.warning(self._format_message(message), **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        self.logger.error(self._format_message(message), **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        self.logger.critical(self._format_message(message), **kwargs)


class AgentLogger(TaskLogger):
    """Agent 日志器"""
    
    def __init__(self, agent_name: str, task_id: str):
        super().__init__(task_id, get_logger("agent"))
        self.agent_name = agent_name
    
    def _format_message(self, message: str) -> str:
        return f"[{self.agent_name}] [Task {self.task_id}] {message}"
    
    def tool_call(self, tool_name: str, args: Dict[str, Any]) -> None:
        self.info(f"调用工具: {tool_name}, 参数: {args}")
    
    def tool_result(self, tool_name: str, success: bool, result: str) -> None:
        status = "成功" if success else "失败"
        self.info(f"工具 {tool_name} 执行{status}: {result}")
    
    def thought(self, content: str) -> None:
        self.debug(f"思考: {content}")

