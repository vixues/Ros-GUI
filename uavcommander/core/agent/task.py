# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
import uuid
import os
from typing import (
    Optional,
    Dict,
    List,
    Any,
    AsyncGenerator,
    Callable,
    Awaitable,
    Union,
    TypeVar,
    Set,
)
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class GeminiEventType(Enum):
    Content = "content"
    ToolCallRequest = "tool_call_request"
    ToolCallResponse = "tool_call_response"
    ToolCallConfirmation = "tool_call_confirmation"
    UserCancelled = "user_cancelled"
    Thought = "thought"
    Citation = "citation"
    ChatCompressed = "chat_compressed"
    Finished = "finished"
    Error = "error"


class ToolConfirmationOutcome(Enum):
    ProceedOnce = "proceed_once"
    Cancel = "cancel"
    ProceedAlways = "proceed_always"
    ProceedAlwaysServer = "proceed_always_server"
    ProceedAlwaysTool = "proceed_always_tool"
    ModifyWithEditor = "modify_with_editor"


class ApprovalMode(Enum):
    YOLO = "yolo"
    NORMAL = "normal"


class MCPServerStatus(Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class CoderAgentEvent(Enum):
    StateChangeEvent = "state_change"
    ToolCallUpdateEvent = "tool_call_update"
    ToolCallConfirmationEvent = "tool_call_confirmation"
    TextContentEvent = "text_content"
    ThoughtEvent = "thought"
    CitationEvent = "citation"


# Type aliases
TaskState = str  # "submitted" | "working" | "input-required" | "completed" | "failed" | "cancelled"
UserTierId = str
AnsiOutput = List[List[Dict[str, str]]]


@dataclass
class Part:
    kind: str
    text: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


@dataclass
class Message:
    kind: str
    role: str
    parts: List[Part]
    message_id: str
    task_id: str
    context_id: str


@dataclass
class Artifact:
    artifact_id: str
    parts: List[Part]


@dataclass
class ToolCallRequestInfo:
    call_id: str
    name: str
    args: Optional[Dict[str, Any]] = None


@dataclass
class ToolConfirmationDetails:
    type: str
    on_confirm: Callable[[ToolConfirmationOutcome, Optional[Dict[str, Any]]], Awaitable[None]]


@dataclass
class ToolCallResponse:
    response_parts: Union[List[Any], Any]


@dataclass
class CompletedToolCall:
    request: ToolCallRequestInfo
    response: ToolCallResponse


@dataclass
class ToolCall:
    request: ToolCallRequestInfo
    status: str
    tool: Optional[Dict[str, Any]] = None
    confirmation_details: Optional[ToolConfirmationDetails] = None
    live_output: Optional[str] = None
    response: Optional[ToolCallResponse] = None


@dataclass
class ThoughtSummary:
    subject: Optional[str] = None
    description: Optional[str] = None


@dataclass
class CoderAgentMessage:
    kind: CoderAgentEvent


@dataclass
class StateChange(CoderAgentMessage):
    pass


@dataclass
class ToolCallUpdate(CoderAgentMessage):
    pass


@dataclass
class TextContent(CoderAgentMessage):
    pass


@dataclass
class Thought(CoderAgentMessage):
    pass


@dataclass
class Citation(CoderAgentMessage):
    pass


@dataclass
class TaskMetadata:
    id: str
    context_id: str
    task_state: TaskState
    model: str
    mcp_servers: List[Dict[str, Any]]
    available_tools: List[Dict[str, Any]]


@dataclass
class TaskStatusUpdateEvent:
    kind: str
    task_id: str
    context_id: str
    status: Dict[str, Any]
    final: bool
    metadata: Dict[str, Any]


@dataclass
class TaskArtifactUpdateEvent:
    kind: str
    task_id: str
    context_id: str
    artifact: Artifact
    append: bool
    last_chunk: bool


@dataclass
class ServerGeminiStreamEvent:
    type: GeminiEventType
    value: Any
    trace_id: Optional[str] = None


@dataclass
class ServerGeminiErrorEvent(ServerGeminiStreamEvent):
    pass


@dataclass
class RequestContext:
    user_message: Message


class ToolConfirmationPayload:
    def __init__(self, new_content: Optional[str] = None):
        self.new_content = new_content


class ExecutionEventBus:
    """Event bus for publishing task events."""
    
    def __init__(self):
        self._subscribers: List[Callable[[Any], None]] = []
    
    def subscribe(self, callback: Callable[[Any], None]) -> None:
        self._subscribers.append(callback)
    
    def publish(self, event: Any) -> None:
        for subscriber in self._subscribers:
            try:
                subscriber(event)
            except Exception as e:
                logger.error(f"Error in event subscriber: {e}")


class GeminiClient:
    """Client for interacting with Gemini API."""
    
    def __init__(self):
        self._history: List[Dict[str, Any]] = []
    
    def add_history(self, entry: Dict[str, Any]) -> None:
        self._history.append(entry)
    
    async def send_message_stream(
        self,
        parts: List[Any],
        aborted: asyncio.Event,
        prompt_id: str = "",
    ) -> AsyncGenerator[ServerGeminiStreamEvent, None]:
        """Send message to LLM and stream responses."""
        # Placeholder implementation - should be overridden or configured
        yield ServerGeminiStreamEvent(
            type=GeminiEventType.Finished,
            value=None,
        )


class ToolRegistry:
    """Registry for available tools."""
    
    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._server_tools: Dict[str, List[Dict[str, Any]]] = {}
    
    def get_tools_by_server(self, server_name: str) -> List[Dict[str, Any]]:
        return self._server_tools.get(server_name, [])
    
    def get_all_tools(self) -> List[Dict[str, Any]]:
        return list(self._tools.values())
    
    def register_tool(self, tool: Dict[str, Any], server_name: Optional[str] = None) -> None:
        self._tools[tool["name"]] = tool
        if server_name:
            if server_name not in self._server_tools:
                self._server_tools[server_name] = []
            self._server_tools[server_name].append(tool)


class MCPClientManager:
    """Manager for MCP server connections."""
    
    def __init__(self):
        self._servers: Dict[str, Any] = {}
    
    def get_mcp_servers(self) -> Dict[str, Any]:
        return self._servers


class Config:
    """Configuration for the task."""
    
    def __init__(
        self,
        model: str = "gemini-pro",
        approval_mode: ApprovalMode = ApprovalMode.NORMAL,
        user_tier: Optional[UserTierId] = None,
    ):
        self._model = model
        self._approval_mode = approval_mode
        self._user_tier = user_tier
        self._tool_registry = ToolRegistry()
        self._mcp_client_manager = MCPClientManager()
        self._gemini_client = GeminiClient()
        self._fallback_model_handler: Optional[Callable[[], Awaitable[str]]] = None
    
    def get_model(self) -> str:
        return self._model
    
    def get_approval_mode(self) -> ApprovalMode:
        return self._approval_mode
    
    def get_user_tier(self) -> Optional[UserTierId]:
        return self._user_tier
    
    async def get_tool_registry(self) -> ToolRegistry:
        return self._tool_registry
    
    def get_mcp_client_manager(self) -> Optional[MCPClientManager]:
        return self._mcp_client_manager
    
    def get_gemini_client(self) -> GeminiClient:
        return self._gemini_client
    
    def set_fallback_model_handler(
        self, handler: Callable[[], Awaitable[str]]
    ) -> None:
        self._fallback_model_handler = handler


# Global MCP server statuses
_mcp_server_statuses: Dict[str, MCPServerStatus] = {}


def get_all_mcp_server_statuses() -> Dict[str, MCPServerStatus]:
    return _mcp_server_statuses.copy()


def is_node_error(err: Exception) -> bool:
    """Check if error is a file system error."""
    return isinstance(err, (FileNotFoundError, IOError, OSError))


def parse_and_format_api_error(error_event: Any) -> str:
    """Parse and format API error message."""
    if hasattr(error_event, "error") and hasattr(error_event.error, "message"):
        return error_event.error.message
    return str(error_event)


def safe_literal_replace(content: str, old_string: str, new_string: str) -> str:
    """Safely replace string without regex interpretation."""
    return content.replace(old_string, new_string, 1)


class CoreToolScheduler:
    """Scheduler for executing tool calls."""
    
    def __init__(
        self,
        output_update_handler: Callable[[str, Union[str, AnsiOutput]], None],
        on_all_tool_calls_complete: Callable[[List[CompletedToolCall]], Awaitable[None]],
        on_tool_calls_update: Callable[[List[ToolCall]], None],
        get_preferred_editor: Callable[[], str],
        config: Config,
    ):
        self._output_update_handler = output_update_handler
        self._on_all_tool_calls_complete = on_all_tool_calls_complete
        self._on_tool_calls_update = on_tool_calls_update
        self._get_preferred_editor = get_preferred_editor
        self._config = config
        self._pending_calls: Dict[str, ToolCall] = {}
    
    async def schedule(
        self,
        requests: List[ToolCallRequestInfo],
        abort_signal: asyncio.Event,
    ) -> None:
        """Schedule tool calls for execution."""
        tool_calls = []
        for request in requests:
            tool_call = ToolCall(
                request=request,
                status="pending",
            )
            self._pending_calls[request.call_id] = tool_call
            tool_calls.append(tool_call)
        
        # Notify about pending tool calls
        self._on_tool_calls_update(tool_calls)
        
        # Execute tool calls (simplified implementation)
        completed_calls = []
        for tool_call in tool_calls:
            if abort_signal.is_set():
                tool_call.status = "cancelled"
                continue
            
            tool_call.status = "executing"
            self._on_tool_calls_update([tool_call])
            
            # Simulate tool execution
            try:
                # Placeholder for actual tool execution
                tool_call.status = "success"
                tool_call.response = ToolCallResponse(response_parts=[])
                completed_calls.append(CompletedToolCall(
                    request=tool_call.request,
                    response=tool_call.response,
                ))
            except Exception as e:
                tool_call.status = "error"
                logger.error(f"Tool call failed: {e}")
            
            self._on_tool_calls_update([tool_call])
        
        if completed_calls:
            await self._on_all_tool_calls_complete(completed_calls)


class Task:
    """Represents a task being executed by the agent."""
    
    def __init__(
        self,
        id: str,
        context_id: str,
        config: Config,
        event_bus: Optional[ExecutionEventBus] = None,
    ):
        self.id = id
        self.context_id = context_id
        self.config = config
        self.scheduler = self._create_scheduler()
        self.gemini_client = self.config.get_gemini_client()
        self.pending_tool_confirmation_details: Dict[str, ToolConfirmationDetails] = {}
        self.task_state: TaskState = "submitted"
        self.event_bus = event_bus
        self.completed_tool_calls: List[CompletedToolCall] = []
        self.skip_final_true_after_inline_edit = False
        
        # For tool waiting logic
        self._pending_tool_calls: Dict[str, str] = {}  # tool_call_id -> status
        self._tool_completion_event: asyncio.Event = asyncio.Event()
        self._tool_completion_error: Optional[Exception] = None
        
        self._reset_tool_completion_promise()
        
        # Set fallback model handler
        self.config.set_fallback_model_handler(self._fallback_handler)
    
    async def _fallback_handler(self) -> str:
        """Handler for fallback model - returns 'stop' to stop without retrying."""
        return "stop"
    
    @classmethod
    async def create(
        cls,
        id: str,
        context_id: str,
        config: Config,
        event_bus: Optional[ExecutionEventBus] = None,
    ) -> "Task":
        """Factory method to create a Task instance."""
        return cls(id, context_id, config, event_bus)
    
    async def get_metadata(self) -> TaskMetadata:
        """Get metadata about the task."""
        tool_registry = await self.config.get_tool_registry()
        mcp_client_manager = self.config.get_mcp_client_manager()
        mcp_servers = mcp_client_manager.get_mcp_servers() if mcp_client_manager else {}
        server_statuses = get_all_mcp_server_statuses()
        
        servers = []
        for server_name in mcp_servers.keys():
            status = server_statuses.get(server_name, MCPServerStatus.DISCONNECTED)
            tools = tool_registry.get_tools_by_server(server_name)
            server_info = {
                "name": server_name,
                "status": status,
                "tools": [
                    {
                        "name": tool.get("name"),
                        "description": tool.get("description"),
                        "parameter_schema": tool.get("schema", {}).get("parameters"),
                    }
                    for tool in tools
                ],
            }
            servers.append(server_info)
        
        available_tools = [
            {
                "name": tool.get("name"),
                "description": tool.get("description"),
                "parameter_schema": tool.get("schema", {}).get("parameters"),
            }
            for tool in tool_registry.get_all_tools()
        ]
        
        return TaskMetadata(
            id=self.id,
            context_id=self.context_id,
            task_state=self.task_state,
            model=self.config.get_model(),
            mcp_servers=servers,
            available_tools=available_tools,
        )
    
    def _reset_tool_completion_promise(self) -> None:
        """Reset the tool completion event."""
        self._tool_completion_event = asyncio.Event()
        self._tool_completion_error = None
        
        # If there are no pending calls when reset, set immediately
        if len(self._pending_tool_calls) == 0:
            self._tool_completion_event.set()
    
    def _register_tool_call(self, tool_call_id: str, status: str) -> None:
        """Register a tool call as pending."""
        was_empty = len(self._pending_tool_calls) == 0
        self._pending_tool_calls[tool_call_id] = status
        
        if was_empty:
            self._reset_tool_completion_promise()
        
        logger.info(
            f"[Task] Registered tool call: {tool_call_id}. "
            f"Pending: {len(self._pending_tool_calls)}"
        )
    
    def _resolve_tool_call(self, tool_call_id: str) -> None:
        """Resolve a pending tool call."""
        if tool_call_id in self._pending_tool_calls:
            del self._pending_tool_calls[tool_call_id]
            logger.info(
                f"[Task] Resolved tool call: {tool_call_id}. "
                f"Pending: {len(self._pending_tool_calls)}"
            )
            
            if len(self._pending_tool_calls) == 0:
                self._tool_completion_event.set()
    
    async def wait_for_pending_tools(self) -> None:
        """Wait for all pending tool calls to complete."""
        if len(self._pending_tool_calls) == 0:
            return
        
        logger.info(
            f"[Task] Waiting for {len(self._pending_tool_calls)} pending tool(s)..."
        )
        
        await self._tool_completion_event.wait()
        
        if self._tool_completion_error:
            raise self._tool_completion_error
    
    def cancel_pending_tools(self, reason: str) -> None:
        """Cancel all pending tool calls."""
        if len(self._pending_tool_calls) > 0:
            logger.info(
                f"[Task] Cancelling all {len(self._pending_tool_calls)} "
                f"pending tool calls. Reason: {reason}"
            )
        
        self._tool_completion_error = Exception(reason)
        self._tool_completion_event.set()
        self._pending_tool_calls.clear()
        
        # Reset the promise for any future operations
        self._reset_tool_completion_promise()
    
    def _create_text_message(
        self,
        text: str,
        role: str = "agent",
    ) -> Message:
        """Create a text message."""
        return Message(
            kind="message",
            role=role,
            parts=[Part(kind="text", text=text)],
            message_id=str(uuid.uuid4()),
            task_id=self.id,
            context_id=self.context_id,
        )
    
    def _create_status_update_event(
        self,
        state_to_report: TaskState,
        coder_agent_message: CoderAgentMessage,
        message: Optional[Message] = None,
        final: bool = False,
        timestamp: Optional[str] = None,
        metadata_error: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> TaskStatusUpdateEvent:
        """Create a status update event."""
        metadata: Dict[str, Any] = {
            "coder_agent": {
                "kind": coder_agent_message.kind.value,
            },
            "model": self.config.get_model(),
        }
        
        user_tier = self.config.get_user_tier()
        if user_tier:
            metadata["user_tier"] = user_tier
        
        if metadata_error:
            metadata["error"] = metadata_error
        
        if trace_id:
            metadata["trace_id"] = trace_id
        
        status_dict: Dict[str, Any] = {
            "state": state_to_report,
            "timestamp": timestamp or datetime.now().isoformat(),
        }
        
        if message:
            status_dict["message"] = {
                "kind": message.kind,
                "role": message.role,
                "parts": [
                    {"kind": p.kind, "text": p.text, "data": p.data}
                    for p in message.parts
                ],
                "message_id": message.message_id,
                "task_id": message.task_id,
                "context_id": message.context_id,
            }
        
        return TaskStatusUpdateEvent(
            kind="status-update",
            task_id=self.id,
            context_id=self.context_id,
            status=status_dict,
            final=final,
            metadata=metadata,
        )
    
    def set_task_state_and_publish_update(
        self,
        new_state: TaskState,
        coder_agent_message: CoderAgentMessage,
        message_text: Optional[str] = None,
        message_parts: Optional[List[Part]] = None,
        final: bool = False,
        metadata_error: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> None:
        """Set task state and publish status update."""
        self.task_state = new_state
        message: Optional[Message] = None
        
        if message_text:
            message = self._create_text_message(message_text)
        elif message_parts:
            message = Message(
                kind="message",
                role="agent",
                parts=message_parts,
                message_id=str(uuid.uuid4()),
                task_id=self.id,
                context_id=self.context_id,
            )
        
        event = self._create_status_update_event(
            self.task_state,
            coder_agent_message,
            message,
            final,
            None,
            metadata_error,
            trace_id,
        )
        
        if self.event_bus:
            self.event_bus.publish(event)
    
    def _scheduler_output_update(
        self,
        tool_call_id: str,
        output_chunk: Union[str, AnsiOutput],
    ) -> None:
        """Handle scheduler output updates."""
        if isinstance(output_chunk, str):
            output_as_text = output_chunk
        else:
            lines = []
            for line in output_chunk:
                line_text = "".join(token.get("text", "") for token in line)
                lines.append(line_text)
            output_as_text = "\n".join(lines)
        
        logger.info(
            f"[Task] Scheduler output update for tool call {tool_call_id}: "
            f"{output_as_text}"
        )
        
        artifact = Artifact(
            artifact_id=f"tool-{tool_call_id}-output",
            parts=[Part(kind="text", text=output_as_text)],
        )
        
        artifact_event = TaskArtifactUpdateEvent(
            kind="artifact-update",
            task_id=self.id,
            context_id=self.context_id,
            artifact=artifact,
            append=True,
            last_chunk=False,
        )
        
        if self.event_bus:
            self.event_bus.publish(artifact_event)
    
    async def _scheduler_all_tool_calls_complete(
        self,
        completed_tool_calls: List[CompletedToolCall],
    ) -> None:
        """Handle completion of all tool calls in a batch."""
        logger.info(
            "[Task] All tool calls completed by scheduler (batch): "
            f"{[tc.request.call_id for tc in completed_tool_calls]}"
        )
        
        self.completed_tool_calls.extend(completed_tool_calls)
        
        for tc in completed_tool_calls:
            self._resolve_tool_call(tc.request.call_id)
    
    def _scheduler_tool_calls_update(self, tool_calls: List[ToolCall]) -> None:
        """Handle tool call status updates from scheduler."""
        logger.info(
            "[Task] Scheduler tool calls updated: "
            f"{[f'{tc.request.call_id} ({tc.status})' for tc in tool_calls]}"
        )
        
        # Update state and send continuous, non-final updates
        for tc in tool_calls:
            previous_status = self._pending_tool_calls.get(tc.request.call_id)
            has_changed = previous_status != tc.status
            
            # Resolve tool call if it has reached a terminal state
            if tc.status in ["success", "error", "cancelled"]:
                self._resolve_tool_call(tc.request.call_id)
            else:
                # This will update the map
                self._register_tool_call(tc.request.call_id, tc.status)
            
            if tc.status == "awaiting_approval" and tc.confirmation_details:
                self.pending_tool_confirmation_details[tc.request.call_id] = (
                    tc.confirmation_details
                )
            
            # Only send an update if the status has actually changed
            if has_changed:
                if tc.status == "awaiting_approval":
                    coder_agent_message = CoderAgentMessage(
                        kind=CoderAgentEvent.ToolCallConfirmationEvent
                    )
                else:
                    coder_agent_message = CoderAgentMessage(
                        kind=CoderAgentEvent.ToolCallUpdateEvent
                    )
                
                message = self._tool_status_message(tc, self.id, self.context_id)
                
                event = self._create_status_update_event(
                    self.task_state,
                    coder_agent_message,
                    message,
                    False,  # Always false for these continuous updates
                )
                
                if self.event_bus:
                    self.event_bus.publish(event)
        
        if self.config.get_approval_mode() == ApprovalMode.YOLO:
            logger.info("[Task] YOLO mode enabled. Auto-approving all tool calls.")
            for tc in tool_calls:
                if tc.status == "awaiting_approval" and tc.confirmation_details:
                    asyncio.create_task(
                        tc.confirmation_details.on_confirm(
                            ToolConfirmationOutcome.ProceedOnce, None
                        )
                    )
                    if tc.request.call_id in self.pending_tool_confirmation_details:
                        del self.pending_tool_confirmation_details[tc.request.call_id]
            return
        
        all_pending_statuses = list(self._pending_tool_calls.values())
        is_awaiting_approval = any(
            status == "awaiting_approval" for status in all_pending_statuses
        )
        is_executing = any(status == "executing" for status in all_pending_statuses)
        
        # The turn is complete and requires user input if at least one tool
        # is waiting for the user's decision, and no other tool is actively
        # running in the background.
        if (
            is_awaiting_approval
            and not is_executing
            and not self.skip_final_true_after_inline_edit
        ):
            self.skip_final_true_after_inline_edit = False
            
            # We don't need to send another message, just a final status update.
            self.set_task_state_and_publish_update(
                "input-required",
                StateChange(kind=CoderAgentEvent.StateChangeEvent),
                None,
                None,
                True,  # final
            )
    
    def _create_scheduler(self) -> CoreToolScheduler:
        """Create the tool scheduler."""
        return CoreToolScheduler(
            output_update_handler=self._scheduler_output_update,
            on_all_tool_calls_complete=self._scheduler_all_tool_calls_complete,
            on_tool_calls_update=self._scheduler_tool_calls_update,
            get_preferred_editor=lambda: "vscode",
            config=self.config,
        )
    
    def _pick_fields(
        self,
        from_obj: Any,
        *fields: str,
    ) -> Dict[str, Any]:
        """Pick specific fields from an object."""
        result = {}
        for field in fields:
            if hasattr(from_obj, field):
                result[field] = getattr(from_obj, field)
            elif isinstance(from_obj, dict) and field in from_obj:
                result[field] = from_obj[field]
        return result
    
    def _tool_status_message(
        self,
        tc: ToolCall,
        task_id: str,
        context_id: str,
    ) -> Message:
        """Create a tool status message."""
        message_parts: List[Part] = []
        
        # Create a serializable version of the ToolCall
        serializable_tool_call = {
            "request": {
                "call_id": tc.request.call_id,
                "name": tc.request.name,
                "args": tc.request.args,
            },
            "status": tc.status,
        }
        
        if tc.confirmation_details:
            serializable_tool_call["confirmation_details"] = {
                "type": tc.confirmation_details.type,
            }
        
        if tc.live_output:
            serializable_tool_call["live_output"] = tc.live_output
        
        if tc.response:
            serializable_tool_call["response"] = {
                "response_parts": tc.response.response_parts,
            }
        
        if tc.tool:
            serializable_tool_call["tool"] = self._pick_fields(
                tc.tool,
                "name",
                "display_name",
                "description",
                "kind",
                "is_output_markdown",
                "can_update_output",
                "schema",
                "parameter_schema",
            )
        
        message_parts.append(Part(kind="data", data=serializable_tool_call))
        
        return Message(
            kind="message",
            role="agent",
            parts=message_parts,
            message_id=str(uuid.uuid4()),
            task_id=task_id,
            context_id=context_id,
        )
    
    async def _get_proposed_content(
        self,
        file_path: str,
        old_string: str,
        new_string: str,
    ) -> str:
        """Get proposed content after applying replacement."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                current_content = f.read()
            
            is_new_file = old_string == "" and current_content == ""
            return self._apply_replacement(
                current_content, old_string, new_string, is_new_file
            )
        except FileNotFoundError:
            return ""
        except Exception as err:
            if not is_node_error(err):
                raise
            return ""
    
    def _apply_replacement(
        self,
        current_content: Optional[str],
        old_string: str,
        new_string: str,
        is_new_file: bool,
    ) -> str:
        """Apply string replacement to content."""
        if is_new_file:
            return new_string
        
        if current_content is None:
            # Should not happen if not a new file
            return new_string if old_string == "" else ""
        
        # If old_string is empty and it's not a new file, do not modify the content
        if old_string == "" and not is_new_file:
            return current_content
        
        # Use safe literal replacement
        return safe_literal_replace(current_content, old_string, new_string)
    
    async def schedule_tool_calls(
        self,
        requests: List[ToolCallRequestInfo],
        abort_signal: asyncio.Event,
    ) -> None:
        """Schedule tool calls for execution."""
        if not requests:
            return
        
        updated_requests = []
        for request in requests:
            if (
                request.name == "replace"
                and request.args
                and not request.args.get("newContent")
                and request.args.get("file_path")
                and request.args.get("old_string")
                and request.args.get("new_string")
            ):
                new_content = await self._get_proposed_content(
                    request.args["file_path"],
                    request.args["old_string"],
                    request.args["new_string"],
                )
                updated_args = {**request.args, "newContent": new_content}
                updated_requests.append(
                    ToolCallRequestInfo(
                        call_id=request.call_id,
                        name=request.name,
                        args=updated_args,
                    )
                )
            else:
                updated_requests.append(request)
        
        logger.info(
            f"[Task] Scheduling batch of {len(updated_requests)} tool calls."
        )
        
        state_change = StateChange(kind=CoderAgentEvent.StateChangeEvent)
        self.set_task_state_and_publish_update("working", state_change)
        
        await self.scheduler.schedule(updated_requests, abort_signal)
    
    async def accept_agent_message(
        self,
        event: ServerGeminiStreamEvent,
    ) -> None:
        """Accept and process an agent message event."""
        state_change = StateChange(kind=CoderAgentEvent.StateChangeEvent)
        trace_id = getattr(event, "trace_id", None)
        
        if event.type == GeminiEventType.Content:
            logger.info("[Task] Sending agent message content...")
            self._send_text_content(event.value, trace_id)
        
        elif event.type == GeminiEventType.ToolCallRequest:
            # This is now handled by the agent loop
            logger.warning(
                "[Task] A single tool call request was passed to accept_agent_message. "
                "This should be handled in a batch by the agent. Ignoring."
            )
        
        elif event.type == GeminiEventType.ToolCallResponse:
            logger.info(
                f"[Task] Received tool call response from LLM (part of generation): "
                f"{event.value}"
            )
        
        elif event.type == GeminiEventType.ToolCallConfirmation:
            logger.info(
                f"[Task] Received tool call confirmation request from LLM: "
                f"{event.value.request.call_id}"
            )
            self.pending_tool_confirmation_details[event.value.request.call_id] = (
                event.value.details
            )
        
        elif event.type == GeminiEventType.UserCancelled:
            logger.info("[Task] Received user cancelled event from LLM stream.")
            self.cancel_pending_tools("User cancelled via LLM stream event")
            self.set_task_state_and_publish_update(
                "input-required",
                state_change,
                "Task cancelled by user",
                None,
                True,
                None,
                trace_id,
            )
        
        elif event.type == GeminiEventType.Thought:
            logger.info("[Task] Sending agent thought...")
            self._send_thought(event.value, trace_id)
        
        elif event.type == GeminiEventType.Citation:
            logger.info("[Task] Received citation from LLM stream.")
            self._send_citation(event.value)
        
        elif event.type == GeminiEventType.ChatCompressed:
            pass
        
        elif event.type == GeminiEventType.Finished:
            logger.info(f"[Task {self.id}] Agent finished its turn.")
        
        elif event.type == GeminiEventType.Error:
            error_event = event
            error_message = "Unknown error from LLM stream"
            if hasattr(error_event.value, "error"):
                error_message = getattr(
                    error_event.value.error, "message", error_message
                )
            
            logger.error(
                f"[Task] Received error event from LLM stream: {error_message}"
            )
            
            err_message = "Unknown error from LLM stream"
            if error_event.value:
                err_message = parse_and_format_api_error(error_event.value)
            
            self.cancel_pending_tools(f"LLM stream error: {error_message}")
            self.set_task_state_and_publish_update(
                self.task_state,
                state_change,
                f"Agent Error, unknown agent message: {error_message}",
                None,
                False,
                err_message,
                trace_id,
            )
        
        else:
            # Default case for unknown event types
            error_message = "Unknown event type"
            logger.error(f"[Task] Unknown event type: {event.type}")
            self.set_task_state_and_publish_update(
                self.task_state,
                state_change,
                f"Agent Error, unknown agent message: {error_message}",
                None,
                False,
                error_message,
                trace_id,
            )
    
    async def _handle_tool_confirmation_part(self, part: Part) -> bool:
        """Handle a tool confirmation part from user message."""
        if (
            part.kind != "data"
            or not part.data
            or not isinstance(part.data.get("callId"), str)
            or not isinstance(part.data.get("outcome"), str)
        ):
            return False
        
        call_id = part.data["callId"]
        outcome_string = part.data["outcome"]
        confirmation_outcome: Optional[ToolConfirmationOutcome] = None
        
        outcome_mapping = {
            "proceed_once": ToolConfirmationOutcome.ProceedOnce,
            "cancel": ToolConfirmationOutcome.Cancel,
            "proceed_always": ToolConfirmationOutcome.ProceedAlways,
            "proceed_always_server": ToolConfirmationOutcome.ProceedAlwaysServer,
            "proceed_always_tool": ToolConfirmationOutcome.ProceedAlwaysTool,
            "modify_with_editor": ToolConfirmationOutcome.ModifyWithEditor,
        }
        
        confirmation_outcome = outcome_mapping.get(outcome_string)
        
        if confirmation_outcome is None:
            logger.warning(
                f'[Task] Unknown tool confirmation outcome: "{outcome_string}" '
                f"for callId: {call_id}"
            )
            return False
        
        confirmation_details = self.pending_tool_confirmation_details.get(call_id)
        
        if not confirmation_details:
            logger.warning(
                f"[Task] Received tool confirmation for unknown or already "
                f"processed callId: {call_id}"
            )
            return False
        
        logger.info(
            f"[Task] Handling tool confirmation for callId: {call_id} "
            f"with outcome: {outcome_string}"
        )
        
        try:
            # Temporarily unset GCP environment variables
            gcp_project = os.environ.get("GOOGLE_CLOUD_PROJECT")
            gcp_creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
            
            try:
                if "GOOGLE_CLOUD_PROJECT" in os.environ:
                    del os.environ["GOOGLE_CLOUD_PROJECT"]
                if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
                    del os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
                
                # Handle edit tool call with updated payload
                if confirmation_details.type == "edit":
                    payload = None
                    if part.data.get("newContent"):
                        payload = {"new_content": part.data["newContent"]}
                    
                    self.skip_final_true_after_inline_edit = payload is not None
                    await confirmation_details.on_confirm(confirmation_outcome, payload)
                else:
                    await confirmation_details.on_confirm(confirmation_outcome, None)
            
            finally:
                # Restore GCP environment variables
                if gcp_project:
                    os.environ["GOOGLE_CLOUD_PROJECT"] = gcp_project
                if gcp_creds:
                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = gcp_creds
            
            # Do not delete if modifying
            if confirmation_outcome != ToolConfirmationOutcome.ModifyWithEditor:
                if call_id in self.pending_tool_confirmation_details:
                    del self.pending_tool_confirmation_details[call_id]
            
            return True
        
        except Exception as error:
            logger.error(
                f"[Task] Error during tool confirmation for callId {call_id}: {error}"
            )
            
            # Resolve it as it won't proceed
            self._resolve_tool_call(call_id)
            
            error_message_text = (
                str(error) if isinstance(error, Exception)
                else f"Error processing tool confirmation for {call_id}"
            )
            
            message = self._create_text_message(error_message_text)
            tool_call_update = ToolCallUpdate(kind=CoderAgentEvent.ToolCallUpdateEvent)
            
            event = self._create_status_update_event(
                self.task_state,
                tool_call_update,
                message,
                False,
            )
            
            if self.event_bus:
                self.event_bus.publish(event)
            
            return False
    
    def get_and_clear_completed_tools(self) -> List[CompletedToolCall]:
        """Get and clear completed tool calls."""
        tools = list(self.completed_tool_calls)
        self.completed_tool_calls = []
        return tools
    
    def add_tool_responses_to_history(
        self,
        completed_tools: List[CompletedToolCall],
    ) -> None:
        """Add tool responses to history without generating a new response."""
        logger.info(
            f"[Task] Adding {len(completed_tools)} tool responses to history "
            "without generating a new response."
        )
        
        for tool_call in completed_tools:
            response_parts = tool_call.response.response_parts
            
            if isinstance(response_parts, list):
                parts = response_parts
            elif isinstance(response_parts, str):
                parts = [{"text": response_parts}]
            else:
                parts = [response_parts]
            
            self.gemini_client.add_history({
                "role": "user",
                "parts": parts,
            })
    
    async def send_completed_tools_to_llm(
        self,
        completed_tool_calls: List[CompletedToolCall],
        aborted: asyncio.Event,
    ) -> AsyncGenerator[ServerGeminiStreamEvent, None]:
        """Send completed tool calls to LLM and yield responses."""
        if not completed_tool_calls:
            return
        
        llm_parts: List[Any] = []
        logger.info(
            f"[Task] Feeding {len(completed_tool_calls)} tool responses to LLM."
        )
        
        for completed_tool_call in completed_tool_calls:
            logger.info(
                f'[Task] Adding tool response for "{completed_tool_call.request.name}" '
                f"(callId: {completed_tool_call.request.call_id}) to LLM input."
            )
            
            response_parts = completed_tool_call.response.response_parts
            if isinstance(response_parts, list):
                llm_parts.extend(response_parts)
            else:
                llm_parts.append(response_parts)
        
        logger.info("[Task] Sending new parts to agent.")
        state_change = StateChange(kind=CoderAgentEvent.StateChangeEvent)
        
        # Set task state to working as we are about to call LLM
        self.set_task_state_and_publish_update("working", state_change)
        
        async for event in self.gemini_client.send_message_stream(
            llm_parts, aborted, ""
        ):
            yield event
    
    async def accept_user_message(
        self,
        request_context: RequestContext,
        aborted: asyncio.Event,
    ) -> AsyncGenerator[ServerGeminiStreamEvent, None]:
        """Accept and process a user message."""
        user_message = request_context.user_message
        llm_parts: List[Any] = []
        any_confirmation_handled = False
        has_content_for_llm = False
        
        for part in user_message.parts:
            confirmation_handled = await self._handle_tool_confirmation_part(part)
            
            if confirmation_handled:
                any_confirmation_handled = True
                continue
            
            if part.kind == "text" and part.text:
                llm_parts.append({"text": part.text})
                has_content_for_llm = True
        
        if has_content_for_llm:
            logger.info("[Task] Sending new parts to LLM.")
            state_change = StateChange(kind=CoderAgentEvent.StateChangeEvent)
            
            # Set task state to working as we are about to call LLM
            self.set_task_state_and_publish_update("working", state_change)
            
            async for event in self.gemini_client.send_message_stream(
                llm_parts, aborted, ""
            ):
                yield event
        
        elif any_confirmation_handled:
            logger.info(
                "[Task] User message only contained tool confirmations. "
                "Scheduler is active. No new input for LLM this turn."
            )
            
            # Ensure task state reflects that scheduler might be working
            if (
                len(self._pending_tool_calls) > 0
                and self.task_state != "input-required"
            ):
                state_change = StateChange(kind=CoderAgentEvent.StateChangeEvent)
                self.set_task_state_and_publish_update("working", state_change)
        
        else:
            logger.info(
                "[Task] No relevant parts in user message for LLM interaction "
                "or tool confirmation."
            )
    
    def _send_text_content(self, content: str, trace_id: Optional[str] = None) -> None:
        """Send text content to event bus."""
        if not content:
            return
        
        logger.info("[Task] Sending text content to event bus.")
        message = self._create_text_message(content)
        text_content = TextContent(kind=CoderAgentEvent.TextContentEvent)
        
        if self.event_bus:
            self.event_bus.publish(
                self._create_status_update_event(
                    self.task_state,
                    text_content,
                    message,
                    False,
                    None,
                    None,
                    trace_id,
                )
            )
    
    def _send_thought(
        self,
        content: ThoughtSummary,
        trace_id: Optional[str] = None,
    ) -> None:
        """Send thought to event bus."""
        if not content.subject and not content.description:
            return
        
        logger.info("[Task] Sending thought to event bus.")
        
        message = Message(
            kind="message",
            role="agent",
            parts=[
                Part(
                    kind="data",
                    data={
                        "subject": content.subject,
                        "description": content.description,
                    },
                )
            ],
            message_id=str(uuid.uuid4()),
            task_id=self.id,
            context_id=self.context_id,
        )
        
        thought = Thought(kind=CoderAgentEvent.ThoughtEvent)
        
        if self.event_bus:
            self.event_bus.publish(
                self._create_status_update_event(
                    self.task_state,
                    thought,
                    message,
                    False,
                    None,
                    None,
                    trace_id,
                )
            )
    
    def _send_citation(self, citation: str) -> None:
        """Send citation to event bus."""
        if not citation or not citation.strip():
            return
        
        logger.info("[Task] Sending citation to event bus.")
        message = self._create_text_message(citation)
        citation_event = Citation(kind=CoderAgentEvent.CitationEvent)
        
        if self.event_bus:
            self.event_bus.publish(
                self._create_status_update_event(
                    self.task_state,
                    citation_event,
                    message,
                )
            )
