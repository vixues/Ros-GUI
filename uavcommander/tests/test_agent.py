"""
Agent 模块测试
"""

import pytest
import asyncio

from core.agent import (
    Context,
    ContextConfig,
    AgentRegistry,
    AgentDefinition,
    AgentType,
    AgentCapability,
    get_agent_registry,
    MockLLM,
    StreamEvent,
    StreamEventType,
)
from core.schema import Message, MessageRole


class TestContext:
    """Context 测试"""
    
    def test_create_context(self):
        """测试创建上下文"""
        context = Context()
        assert context.context_id is not None
        assert context.message_count == 0
    
    def test_add_message(self):
        """测试添加消息"""
        context = Context()
        
        msg = context.add_user_message("Hello")
        assert context.message_count == 1
        assert msg.role == MessageRole.USER
        assert msg.text_content == "Hello"
    
    def test_get_history(self):
        """测试获取历史"""
        context = Context()
        
        context.add_user_message("Message 1")
        context.add_assistant_message("Response 1")
        context.add_user_message("Message 2")
        
        history = context.get_history()
        assert len(history) == 3
        
        # 限制数量
        limited = context.get_history(limit=2)
        assert len(limited) == 2
    
    def test_get_llm_messages(self):
        """测试获取 LLM 格式消息"""
        context = Context()
        
        context.add_user_message("Hello")
        context.add_assistant_message("Hi there!")
        
        messages = context.get_llm_messages()
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"


class TestAgentRegistry:
    """Agent 注册表测试"""
    
    def test_predefined_agents(self):
        """测试预定义代理"""
        registry = get_agent_registry()
        
        # 检查 coordinator
        coordinator = registry.get("coordinator")
        assert coordinator is not None
        assert coordinator.agent_type == AgentType.COORDINATOR
        
        # 检查 formation_agent
        formation = registry.get("formation_agent")
        assert formation is not None
        assert formation.agent_type == AgentType.SPECIALIST
    
    def test_register_agent(self):
        """测试注册代理"""
        registry = get_agent_registry()
        
        custom_agent = AgentDefinition(
            name="custom_agent",
            description="自定义代理",
            agent_type=AgentType.WORKER,
            capabilities=[AgentCapability.TOOL_USE],
        )
        
        registry.register(custom_agent)
        
        retrieved = registry.get("custom_agent")
        assert retrieved is not None
        assert retrieved.name == "custom_agent"
    
    def test_list_by_type(self):
        """测试按类型列出"""
        registry = get_agent_registry()
        
        specialists = registry.list_by_type(AgentType.SPECIALIST)
        assert len(specialists) > 0
        
        for agent in specialists:
            assert agent.agent_type == AgentType.SPECIALIST


class TestMockLLM:
    """MockLLM 测试"""
    
    @pytest.mark.asyncio
    async def test_generate(self):
        """测试生成"""
        llm = MockLLM(responses=["这是测试响应"])
        
        response = await llm.generate([
            {"role": "user", "content": "Hello"}
        ])
        
        assert response.content == "这是测试响应"
    
    @pytest.mark.asyncio
    async def test_generate_stream(self):
        """测试流式生成"""
        llm = MockLLM(responses=["Hello World"])
        
        content = []
        async for event in llm.generate_stream([
            {"role": "user", "content": "Hi"}
        ]):
            if event.type == StreamEventType.CONTENT:
                content.append(event.content)
            elif event.type == StreamEventType.FINISHED:
                break
        
        assert "".join(content) == "Hello World"

