"""
LLM 配置模块

定义 LLM 相关的配置项，支持多种 LLM 提供商。
"""

import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum


class LLMProvider(Enum):
    """LLM 提供商"""
    
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    LOCAL = "local"
    AZURE = "azure"


class ModelCapability(Enum):
    """模型能力"""
    
    CHAT = "chat"
    FUNCTION_CALLING = "function_calling"
    VISION = "vision"
    STREAMING = "streaming"
    LONG_CONTEXT = "long_context"


@dataclass
class ModelConfig:
    """模型配置"""
    
    name: str
    provider: LLMProvider
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 1.0
    capabilities: List[ModelCapability] = field(default_factory=list)
    context_window: int = 8192
    
    # 成本相关
    input_cost_per_1k: float = 0.0
    output_cost_per_1k: float = 0.0


# 预定义模型配置
PREDEFINED_MODELS: Dict[str, ModelConfig] = {
    "gpt-4": ModelConfig(
        name="gpt-4",
        provider=LLMProvider.OPENAI,
        max_tokens=8192,
        temperature=0.7,
        capabilities=[
            ModelCapability.CHAT,
            ModelCapability.FUNCTION_CALLING,
            ModelCapability.STREAMING,
        ],
        context_window=8192,
        input_cost_per_1k=0.03,
        output_cost_per_1k=0.06,
    ),
    "gpt-4-turbo": ModelConfig(
        name="gpt-4-turbo-preview",
        provider=LLMProvider.OPENAI,
        max_tokens=4096,
        temperature=0.7,
        capabilities=[
            ModelCapability.CHAT,
            ModelCapability.FUNCTION_CALLING,
            ModelCapability.VISION,
            ModelCapability.STREAMING,
            ModelCapability.LONG_CONTEXT,
        ],
        context_window=128000,
        input_cost_per_1k=0.01,
        output_cost_per_1k=0.03,
    ),
    "gpt-4o": ModelConfig(
        name="gpt-4o",
        provider=LLMProvider.OPENAI,
        max_tokens=4096,
        temperature=0.7,
        capabilities=[
            ModelCapability.CHAT,
            ModelCapability.FUNCTION_CALLING,
            ModelCapability.VISION,
            ModelCapability.STREAMING,
            ModelCapability.LONG_CONTEXT,
        ],
        context_window=128000,
        input_cost_per_1k=0.005,
        output_cost_per_1k=0.015,
    ),
    "claude-3-opus": ModelConfig(
        name="claude-3-opus-20240229",
        provider=LLMProvider.ANTHROPIC,
        max_tokens=4096,
        temperature=0.7,
        capabilities=[
            ModelCapability.CHAT,
            ModelCapability.FUNCTION_CALLING,
            ModelCapability.VISION,
            ModelCapability.STREAMING,
            ModelCapability.LONG_CONTEXT,
        ],
        context_window=200000,
        input_cost_per_1k=0.015,
        output_cost_per_1k=0.075,
    ),
    "claude-3-sonnet": ModelConfig(
        name="claude-3-sonnet-20240229",
        provider=LLMProvider.ANTHROPIC,
        max_tokens=4096,
        temperature=0.7,
        capabilities=[
            ModelCapability.CHAT,
            ModelCapability.FUNCTION_CALLING,
            ModelCapability.VISION,
            ModelCapability.STREAMING,
            ModelCapability.LONG_CONTEXT,
        ],
        context_window=200000,
        input_cost_per_1k=0.003,
        output_cost_per_1k=0.015,
    ),
    "gemini-pro": ModelConfig(
        name="gemini-pro",
        provider=LLMProvider.GOOGLE,
        max_tokens=8192,
        temperature=0.7,
        capabilities=[
            ModelCapability.CHAT,
            ModelCapability.FUNCTION_CALLING,
            ModelCapability.STREAMING,
        ],
        context_window=32768,
    ),
    "gemini-1.5-pro": ModelConfig(
        name="gemini-1.5-pro",
        provider=LLMProvider.GOOGLE,
        max_tokens=8192,
        temperature=0.7,
        capabilities=[
            ModelCapability.CHAT,
            ModelCapability.FUNCTION_CALLING,
            ModelCapability.VISION,
            ModelCapability.STREAMING,
            ModelCapability.LONG_CONTEXT,
        ],
        context_window=1000000,
    ),
}


@dataclass
class LLMSettings:
    """LLM 设置"""
    
    # 默认模型
    default_model: str = "gpt-4"
    
    # API 配置
    openai_api_key: Optional[str] = None
    openai_api_base: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    azure_api_key: Optional[str] = None
    azure_endpoint: Optional[str] = None
    
    # 请求配置
    request_timeout: float = 120.0
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # 流式配置
    stream_chunk_size: int = 1024
    
    # 模型配置覆盖
    model_overrides: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def __post_init__(self):
        # 从环境变量加载 API keys
        if not self.openai_api_key:
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.anthropic_api_key:
            self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.google_api_key:
            self.google_api_key = os.getenv("GOOGLE_API_KEY")
        if not self.azure_api_key:
            self.azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        if not self.azure_endpoint:
            self.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    
    def get_model_config(self, model_name: str) -> ModelConfig:
        """获取模型配置"""
        if model_name in PREDEFINED_MODELS:
            config = PREDEFINED_MODELS[model_name]
            # 应用覆盖配置
            if model_name in self.model_overrides:
                overrides = self.model_overrides[model_name]
                for key, value in overrides.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
            return config
        
        # 返回默认配置
        return ModelConfig(
            name=model_name,
            provider=LLMProvider.OPENAI,
        )
    
    def get_api_key(self, provider: LLMProvider) -> Optional[str]:
        """获取指定提供商的 API Key"""
        key_map = {
            LLMProvider.OPENAI: self.openai_api_key,
            LLMProvider.ANTHROPIC: self.anthropic_api_key,
            LLMProvider.GOOGLE: self.google_api_key,
            LLMProvider.AZURE: self.azure_api_key,
        }
        return key_map.get(provider)
    
    @classmethod
    def from_env(cls) -> "LLMSettings":
        """从环境变量创建配置"""
        return cls(
            default_model=os.getenv("UAV_DEFAULT_MODEL", "gpt-4"),
            request_timeout=float(os.getenv("UAV_LLM_TIMEOUT", "120.0")),
            max_retries=int(os.getenv("UAV_LLM_MAX_RETRIES", "3")),
        )

