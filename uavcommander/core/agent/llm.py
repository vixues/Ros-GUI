"""
LLM 具体实现模块

实现各种 LLM 提供商的客户端。
"""

import asyncio
import json
from typing import Optional, Dict, List, Any, AsyncGenerator
from dataclasses import dataclass
import logging

from .basellm import BaseLLM, StreamEvent, StreamEventType, LLMResponse
from core.schema import ToolCallRequest, ThoughtSummary
from core.config import LLMSettings, ModelConfig, LLMProvider

logger = logging.getLogger(__name__)


class OpenAILLM(BaseLLM):
    """OpenAI LLM 实现"""
    
    def __init__(
        self,
        settings: Optional[LLMSettings] = None,
        model_config: Optional[ModelConfig] = None,
    ):
        super().__init__(settings, model_config)
        self._client = None
        self._async_client = None
    
    def _get_client(self):
        """获取 OpenAI 客户端"""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self.settings.openai_api_key,
                    base_url=self.settings.openai_api_base,
                    timeout=self.settings.request_timeout,
                )
            except ImportError:
                raise ImportError("请安装 openai: pip install openai")
        return self._client
    
    def _get_async_client(self):
        """获取异步 OpenAI 客户端"""
        if self._async_client is None:
            try:
                from openai import AsyncOpenAI
                self._async_client = AsyncOpenAI(
                    api_key=self.settings.openai_api_key,
                    base_url=self.settings.openai_api_base,
                    timeout=self.settings.request_timeout,
                )
            except ImportError:
                raise ImportError("请安装 openai: pip install openai")
        return self._async_client
    
    async def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> LLMResponse:
        """生成响应"""
        client = self._get_async_client()
        
        request_params = {
            "model": self.model_config.name,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.model_config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.model_config.max_tokens),
        }
        
        if tools:
            request_params["tools"] = tools
            request_params["tool_choice"] = kwargs.get("tool_choice", "auto")
        
        try:
            response = await client.chat.completions.create(**request_params)
            return self._parse_response(response)
        except Exception as e:
            logger.error(f"OpenAI 请求失败: {e}")
            raise
    
    async def generate_stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        abort_signal: Optional[asyncio.Event] = None,
        **kwargs,
    ) -> AsyncGenerator[StreamEvent, None]:
        """流式生成响应"""
        client = self._get_async_client()
        
        request_params = {
            "model": self.model_config.name,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.model_config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.model_config.max_tokens),
            "stream": True,
        }
        
        if tools:
            request_params["tools"] = tools
            request_params["tool_choice"] = kwargs.get("tool_choice", "auto")
        
        try:
            stream = await client.chat.completions.create(**request_params)
            
            current_tool_calls: Dict[int, Dict[str, Any]] = {}
            
            async for chunk in stream:
                # 检查中断信号
                if abort_signal and abort_signal.is_set():
                    yield StreamEvent.finish()
                    return
                
                choice = chunk.choices[0] if chunk.choices else None
                if not choice:
                    continue
                
                delta = choice.delta
                
                # 处理文本内容
                if delta.content:
                    yield StreamEvent.text(delta.content)
                
                # 处理工具调用
                if delta.tool_calls:
                    for tool_call in delta.tool_calls:
                        idx = tool_call.index
                        
                        if idx not in current_tool_calls:
                            current_tool_calls[idx] = {
                                "id": "",
                                "name": "",
                                "arguments": "",
                            }
                        
                        if tool_call.id:
                            current_tool_calls[idx]["id"] = tool_call.id
                        if tool_call.function:
                            if tool_call.function.name:
                                current_tool_calls[idx]["name"] = tool_call.function.name
                            if tool_call.function.arguments:
                                current_tool_calls[idx]["arguments"] += tool_call.function.arguments
                
                # 检查结束
                if choice.finish_reason:
                    # 发送完成的工具调用
                    for tc in current_tool_calls.values():
                        try:
                            args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                            yield StreamEvent.tool(ToolCallRequest(
                                call_id=tc["id"],
                                name=tc["name"],
                                args=args,
                            ))
                        except json.JSONDecodeError:
                            logger.error(f"工具参数解析失败: {tc['arguments']}")
                    
                    yield StreamEvent.finish()
                    return
            
        except Exception as e:
            logger.error(f"OpenAI 流式请求失败: {e}")
            yield StreamEvent.fail(str(e))
    
    def _parse_response(self, response) -> LLMResponse:
        """解析响应"""
        choice = response.choices[0]
        message = choice.message
        
        tool_calls = []
        if message.tool_calls:
            for tc in message.tool_calls:
                try:
                    args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                    tool_calls.append(ToolCallRequest(
                        call_id=tc.id,
                        name=tc.function.name,
                        args=args,
                    ))
                except json.JSONDecodeError:
                    logger.error(f"工具参数解析失败: {tc.function.arguments}")
        
        return LLMResponse(
            content=message.content or "",
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            },
        )


class AnthropicLLM(BaseLLM):
    """Anthropic Claude LLM 实现"""
    
    def __init__(
        self,
        settings: Optional[LLMSettings] = None,
        model_config: Optional[ModelConfig] = None,
    ):
        super().__init__(settings, model_config)
        self._client = None
    
    def _get_client(self):
        """获取 Anthropic 客户端"""
        if self._client is None:
            try:
                from anthropic import AsyncAnthropic
                self._client = AsyncAnthropic(
                    api_key=self.settings.anthropic_api_key,
                    timeout=self.settings.request_timeout,
                )
            except ImportError:
                raise ImportError("请安装 anthropic: pip install anthropic")
        return self._client
    
    async def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> LLMResponse:
        """生成响应"""
        client = self._get_client()
        
        # 分离系统消息和对话消息
        system_prompt = ""
        chat_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                chat_messages.append(msg)
        
        # 转换工具格式
        anthropic_tools = None
        if tools:
            anthropic_tools = self._convert_tools(tools)
        
        request_params = {
            "model": self.model_config.name,
            "messages": chat_messages,
            "max_tokens": kwargs.get("max_tokens", self.model_config.max_tokens),
        }
        
        if system_prompt:
            request_params["system"] = system_prompt
        
        if anthropic_tools:
            request_params["tools"] = anthropic_tools
        
        try:
            response = await client.messages.create(**request_params)
            return self._parse_response(response)
        except Exception as e:
            logger.error(f"Anthropic 请求失败: {e}")
            raise
    
    async def generate_stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        abort_signal: Optional[asyncio.Event] = None,
        **kwargs,
    ) -> AsyncGenerator[StreamEvent, None]:
        """流式生成响应"""
        client = self._get_client()
        
        # 分离系统消息
        system_prompt = ""
        chat_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                chat_messages.append(msg)
        
        anthropic_tools = None
        if tools:
            anthropic_tools = self._convert_tools(tools)
        
        request_params = {
            "model": self.model_config.name,
            "messages": chat_messages,
            "max_tokens": kwargs.get("max_tokens", self.model_config.max_tokens),
            "stream": True,
        }
        
        if system_prompt:
            request_params["system"] = system_prompt
        
        if anthropic_tools:
            request_params["tools"] = anthropic_tools
        
        try:
            async with client.messages.stream(**request_params) as stream:
                current_tool: Optional[Dict[str, Any]] = None
                
                async for event in stream:
                    if abort_signal and abort_signal.is_set():
                        yield StreamEvent.finish()
                        return
                    
                    if event.type == "content_block_start":
                        if hasattr(event.content_block, "type"):
                            if event.content_block.type == "tool_use":
                                current_tool = {
                                    "id": event.content_block.id,
                                    "name": event.content_block.name,
                                    "input": "",
                                }
                    
                    elif event.type == "content_block_delta":
                        if hasattr(event.delta, "text"):
                            yield StreamEvent.text(event.delta.text)
                        elif hasattr(event.delta, "partial_json"):
                            if current_tool:
                                current_tool["input"] += event.delta.partial_json
                    
                    elif event.type == "content_block_stop":
                        if current_tool:
                            try:
                                args = json.loads(current_tool["input"]) if current_tool["input"] else {}
                                yield StreamEvent.tool(ToolCallRequest(
                                    call_id=current_tool["id"],
                                    name=current_tool["name"],
                                    args=args,
                                ))
                            except json.JSONDecodeError:
                                pass
                            current_tool = None
                    
                    elif event.type == "message_stop":
                        yield StreamEvent.finish()
                        return
        
        except Exception as e:
            logger.error(f"Anthropic 流式请求失败: {e}")
            yield StreamEvent.fail(str(e))
    
    def _convert_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """转换工具格式为 Anthropic 格式"""
        anthropic_tools = []
        for tool in tools:
            if tool.get("type") == "function":
                func = tool["function"]
                anthropic_tools.append({
                    "name": func["name"],
                    "description": func.get("description", ""),
                    "input_schema": func.get("parameters", {"type": "object", "properties": {}}),
                })
        return anthropic_tools
    
    def _parse_response(self, response) -> LLMResponse:
        """解析响应"""
        content = ""
        tool_calls = []
        
        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                tool_calls.append(ToolCallRequest(
                    call_id=block.id,
                    name=block.name,
                    args=block.input,
                ))
        
        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=response.stop_reason or "end_turn",
            usage={
                "prompt_tokens": response.usage.input_tokens if response.usage else 0,
                "completion_tokens": response.usage.output_tokens if response.usage else 0,
            },
        )


class MockLLM(BaseLLM):
    """模拟 LLM（用于测试）"""
    
    def __init__(
        self,
        settings: Optional[LLMSettings] = None,
        model_config: Optional[ModelConfig] = None,
        responses: Optional[List[str]] = None,
    ):
        super().__init__(settings, model_config)
        self.responses = responses or ["这是一个模拟响应。"]
        self._response_index = 0
    
    async def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> LLMResponse:
        response = self.responses[self._response_index % len(self.responses)]
        self._response_index += 1
        
        return LLMResponse(
            content=response,
            finish_reason="stop",
        )
    
    async def generate_stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        abort_signal: Optional[asyncio.Event] = None,
        **kwargs,
    ) -> AsyncGenerator[StreamEvent, None]:
        response = self.responses[self._response_index % len(self.responses)]
        self._response_index += 1
        
        # 模拟流式输出
        for char in response:
            if abort_signal and abort_signal.is_set():
                break
            yield StreamEvent.text(char)
            await asyncio.sleep(0.01)
        
        yield StreamEvent.finish()


def create_llm(
    provider: Optional[LLMProvider] = None,
    settings: Optional[LLMSettings] = None,
    model_name: Optional[str] = None,
) -> BaseLLM:
    """
    创建 LLM 实例
    
    Args:
        provider: LLM 提供商
        settings: LLM 设置
        model_name: 模型名称
    
    Returns:
        LLM 实例
    """
    settings = settings or LLMSettings.from_env()
    
    if model_name:
        model_config = settings.get_model_config(model_name)
        provider = provider or model_config.provider
    else:
        model_config = settings.get_model_config(settings.default_model)
        provider = provider or model_config.provider
    
    if provider == LLMProvider.OPENAI:
        return OpenAILLM(settings, model_config)
    elif provider == LLMProvider.ANTHROPIC:
        return AnthropicLLM(settings, model_config)
    elif provider == LLMProvider.LOCAL:
        return MockLLM(settings, model_config)
    else:
        # 默认使用 OpenAI
        return OpenAILLM(settings, model_config)

