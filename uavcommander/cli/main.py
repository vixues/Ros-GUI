"""
CLI 入口模块

UAV Commander 命令行接口入口。
"""

import asyncio
import sys
import argparse
from typing import Optional
import logging

from core.config import (
    Config,
    SystemSettings,
    ApprovalMode,
    Environment,
    get_config,
    set_config,
)
from core.tools import setup_default_tools
from utils import setup_logging, LogConfig, LogLevel

from .repl import REPL
from .commands import CommandHandler


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        prog="uavcommander",
        description="UAV Commander - 基于 LLM 的智能无人机集群控制系统",
    )
    
    parser.add_argument(
        "-v", "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )
    
    parser.add_argument(
        "-m", "--model",
        type=str,
        default="gpt-4",
        help="使用的 LLM 模型 (默认: gpt-4)",
    )
    
    parser.add_argument(
        "--approval-mode",
        type=str,
        choices=["strict", "normal", "yolo"],
        default="normal",
        help="审批模式: strict/normal/yolo (默认: normal)",
    )
    
    parser.add_argument(
        "--simulation",
        action="store_true",
        help="仿真模式（不连接实际无人机）",
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="调试模式",
    )
    
    parser.add_argument(
        "-c", "--command",
        type=str,
        help="直接执行命令（非交互模式）",
    )
    
    parser.add_argument(
        "--no-stream",
        action="store_true",
        help="禁用流式输出",
    )
    
    return parser.parse_args()


def setup_config(args: argparse.Namespace) -> Config:
    """设置配置"""
    # 环境
    if args.simulation:
        environment = Environment.SIMULATION
    elif args.debug:
        environment = Environment.DEVELOPMENT
    else:
        environment = Environment.PRODUCTION
    
    # 审批模式
    approval_mode = ApprovalMode(args.approval_mode)
    
    # 创建配置
    settings = SystemSettings(
        environment=environment,
        debug=args.debug,
        approval_mode=approval_mode,
        log_level="DEBUG" if args.debug else "INFO",
    )
    
    config = Config(system=settings)
    config.set_model(args.model)
    
    set_config(config)
    return config


def setup_logging_from_args(args: argparse.Namespace) -> None:
    """设置日志"""
    log_config = LogConfig(
        level=LogLevel.DEBUG if args.debug else LogLevel.INFO,
        console_colors=True,
        file_enabled=True,
    )
    setup_logging(log_config)


async def run_single_command(command: str, config: Config) -> None:
    """执行单个命令"""
    from core.agent import AgentExecutorFactory
    
    factory = AgentExecutorFactory(config)
    executor = factory.create_coordinator()
    
    if not executor:
        print("❌ 无法创建执行器")
        return
    
    # 输出回调
    def on_output(msg: str):
        print(msg)
    
    executor.on_output(on_output)
    
    print(f"🚀 执行: {command}")
    print("-" * 50)
    
    result = await executor.run(command)
    
    print("-" * 50)
    if result.success:
        print(f"✅ 完成 (轮次: {result.turns}, 工具调用: {result.tool_calls_count})")
    else:
        print(f"❌ 失败: {result.content}")


async def run_repl(config: Config, stream_enabled: bool = True) -> None:
    """运行交互式 REPL"""
    repl = REPL(config, stream_enabled=stream_enabled)
    await repl.run()


def main() -> None:
    """主入口"""
    args = parse_args()
    
    # 设置日志
    setup_logging_from_args(args)
    
    # 设置配置
    config = setup_config(args)
    
    # 设置工具
    setup_default_tools()
    
    # 显示启动信息
    print("=" * 60)
    print("  🚁 UAV Commander - 智能无人机集群控制系统")
    print("=" * 60)
    print(f"  模型: {config.get_model()}")
    print(f"  审批模式: {config.get_approval_mode().value}")
    print(f"  仿真模式: {config.is_simulation()}")
    print("=" * 60)
    print()
    
    try:
        if args.command:
            # 执行单个命令
            asyncio.run(run_single_command(args.command, config))
        else:
            # 启动交互式 REPL
            asyncio.run(run_repl(config, not args.no_stream))
    except KeyboardInterrupt:
        print("\n\n👋 再见！")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

