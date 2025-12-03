"""
Agent 模块

UAV Commander 的核心 Agent 系统。
"""

from .basellm import (
    BaseLLM,
    StreamEvent,
    StreamEventType,
    LLMResponse,
    LLMWithFallback,
)

from .llm import (
    OpenAILLM,
    AnthropicLLM,
    MockLLM,
    create_llm,
)

from .context import (
    Context,
    ContextConfig,
    ContextManager,
    ContextSummary,
    get_context_manager,
)

from .registry import (
    AgentType,
    AgentCapability,
    AgentDefinition,
    AgentRegistry,
    get_agent_registry,
    register_agent,
    get_agent,
    PREDEFINED_AGENTS,
)

from .prompts import (
    PromptTemplate,
    PromptManager,
    get_prompt_manager,
    COORDINATOR_SYSTEM_PROMPT,
    FORMATION_AGENT_PROMPT,
    NAVIGATION_AGENT_PROMPT,
    SEARCH_AGENT_PROMPT,
    TOOL_DESCRIPTIONS,
)

from .scheduler import (
    CoreToolScheduler,
    SchedulerConfig,
)

from .invocation import (
    SubagentInvocation,
    SubagentInvocationBuilder,
    InvocationResult,
)

from .executor import (
    AgentExecutor,
    AgentExecutorFactory,
    ExecutorConfig,
    ExecutorResult,
)

from .automator import (
    Automator,
    AutomatorFactory,
    AutomatorConfig,
    AutomatorResult,
    AutomatorState,
)


__all__ = [
    # basellm
    "BaseLLM",
    "StreamEvent",
    "StreamEventType",
    "LLMResponse",
    "LLMWithFallback",
    # llm
    "OpenAILLM",
    "AnthropicLLM",
    "MockLLM",
    "create_llm",
    # context
    "Context",
    "ContextConfig",
    "ContextManager",
    "ContextSummary",
    "get_context_manager",
    # registry
    "AgentType",
    "AgentCapability",
    "AgentDefinition",
    "AgentRegistry",
    "get_agent_registry",
    "register_agent",
    "get_agent",
    "PREDEFINED_AGENTS",
    # prompts
    "PromptTemplate",
    "PromptManager",
    "get_prompt_manager",
    "COORDINATOR_SYSTEM_PROMPT",
    "FORMATION_AGENT_PROMPT",
    "NAVIGATION_AGENT_PROMPT",
    "SEARCH_AGENT_PROMPT",
    "TOOL_DESCRIPTIONS",
    # scheduler
    "CoreToolScheduler",
    "SchedulerConfig",
    # invocation
    "SubagentInvocation",
    "SubagentInvocationBuilder",
    "InvocationResult",
    # executor
    "AgentExecutor",
    "AgentExecutorFactory",
    "ExecutorConfig",
    "ExecutorResult",
    # automator
    "Automator",
    "AutomatorFactory",
    "AutomatorConfig",
    "AutomatorResult",
    "AutomatorState",
]

