"""
事件总线模块

实现事件驱动的发布订阅机制。
"""

import asyncio
from typing import (
    Optional,
    Dict,
    List,
    Any,
    Callable,
    Awaitable,
    Union,
    Set,
    TypeVar,
    Generic,
)
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import weakref
from collections import defaultdict

from core.schema.events import BaseEvent, EventType

logger = logging.getLogger(__name__)


# 事件处理器类型
EventHandler = Callable[[BaseEvent], None]
AsyncEventHandler = Callable[[BaseEvent], Awaitable[None]]
AnyEventHandler = Union[EventHandler, AsyncEventHandler]


@dataclass
class Subscription:
    """订阅信息"""
    
    id: str
    event_type: Optional[EventType]  # None 表示订阅所有事件
    handler: AnyEventHandler
    is_async: bool = False
    priority: int = 0  # 优先级，数字越大越先执行
    once: bool = False  # 是否只执行一次
    filter_func: Optional[Callable[[BaseEvent], bool]] = None
    
    def matches(self, event: BaseEvent) -> bool:
        """检查事件是否匹配"""
        if self.event_type is not None and event.event_type != self.event_type:
            return False
        if self.filter_func and not self.filter_func(event):
            return False
        return True


class EventBus:
    """事件总线"""
    
    def __init__(self, name: str = "main"):
        self.name = name
        self._subscriptions: Dict[str, Subscription] = {}
        self._type_index: Dict[EventType, Set[str]] = defaultdict(set)
        self._global_subscriptions: Set[str] = set()
        self._subscription_counter = 0
        self._lock = asyncio.Lock()
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
    
    def _generate_subscription_id(self) -> str:
        """生成订阅 ID"""
        self._subscription_counter += 1
        return f"sub_{self._subscription_counter}"
    
    def subscribe(
        self,
        event_type: Optional[EventType],
        handler: AnyEventHandler,
        priority: int = 0,
        once: bool = False,
        filter_func: Optional[Callable[[BaseEvent], bool]] = None,
    ) -> str:
        """
        订阅事件
        
        Args:
            event_type: 事件类型，None 表示订阅所有事件
            handler: 事件处理器
            priority: 优先级
            once: 是否只执行一次
            filter_func: 过滤函数
        
        Returns:
            订阅 ID
        """
        sub_id = self._generate_subscription_id()
        is_async = asyncio.iscoroutinefunction(handler)
        
        subscription = Subscription(
            id=sub_id,
            event_type=event_type,
            handler=handler,
            is_async=is_async,
            priority=priority,
            once=once,
            filter_func=filter_func,
        )
        
        self._subscriptions[sub_id] = subscription
        
        if event_type is None:
            self._global_subscriptions.add(sub_id)
        else:
            self._type_index[event_type].add(sub_id)
        
        logger.debug(f"[EventBus:{self.name}] 添加订阅: {sub_id} -> {event_type}")
        return sub_id
    
    def unsubscribe(self, subscription_id: str) -> bool:
        """取消订阅"""
        if subscription_id not in self._subscriptions:
            return False
        
        subscription = self._subscriptions.pop(subscription_id)
        
        if subscription.event_type is None:
            self._global_subscriptions.discard(subscription_id)
        else:
            self._type_index[subscription.event_type].discard(subscription_id)
        
        logger.debug(f"[EventBus:{self.name}] 移除订阅: {subscription_id}")
        return True
    
    def on(
        self,
        event_type: EventType,
        priority: int = 0,
    ) -> Callable[[AnyEventHandler], AnyEventHandler]:
        """装饰器方式订阅"""
        def decorator(handler: AnyEventHandler) -> AnyEventHandler:
            self.subscribe(event_type, handler, priority)
            return handler
        return decorator
    
    def once(
        self,
        event_type: EventType,
        priority: int = 0,
    ) -> Callable[[AnyEventHandler], AnyEventHandler]:
        """装饰器方式订阅（只执行一次）"""
        def decorator(handler: AnyEventHandler) -> AnyEventHandler:
            self.subscribe(event_type, handler, priority, once=True)
            return handler
        return decorator
    
    def _get_handlers(self, event: BaseEvent) -> List[Subscription]:
        """获取匹配的处理器（按优先级排序）"""
        handlers = []
        
        # 获取特定类型的订阅
        type_subs = self._type_index.get(event.event_type, set())
        for sub_id in type_subs:
            if sub_id in self._subscriptions:
                sub = self._subscriptions[sub_id]
                if sub.matches(event):
                    handlers.append(sub)
        
        # 获取全局订阅
        for sub_id in self._global_subscriptions:
            if sub_id in self._subscriptions:
                sub = self._subscriptions[sub_id]
                if sub.matches(event):
                    handlers.append(sub)
        
        # 按优先级排序
        handlers.sort(key=lambda s: s.priority, reverse=True)
        return handlers
    
    def publish(self, event: BaseEvent) -> None:
        """
        发布事件（同步）
        
        同步执行所有处理器
        """
        handlers = self._get_handlers(event)
        to_remove = []
        
        for subscription in handlers:
            try:
                if subscription.is_async:
                    # 在同步环境中运行异步处理器
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.create_task(subscription.handler(event))
                        else:
                            loop.run_until_complete(subscription.handler(event))
                    except RuntimeError:
                        asyncio.run(subscription.handler(event))
                else:
                    subscription.handler(event)
                
                if subscription.once:
                    to_remove.append(subscription.id)
                    
            except Exception as e:
                logger.error(
                    f"[EventBus:{self.name}] 处理器 {subscription.id} 执行失败: {e}"
                )
        
        # 移除一次性订阅
        for sub_id in to_remove:
            self.unsubscribe(sub_id)
    
    async def publish_async(self, event: BaseEvent) -> None:
        """发布事件（异步）"""
        handlers = self._get_handlers(event)
        to_remove = []
        
        for subscription in handlers:
            try:
                if subscription.is_async:
                    await subscription.handler(event)
                else:
                    subscription.handler(event)
                
                if subscription.once:
                    to_remove.append(subscription.id)
                    
            except Exception as e:
                logger.error(
                    f"[EventBus:{self.name}] 处理器 {subscription.id} 执行失败: {e}"
                )
        
        # 移除一次性订阅
        for sub_id in to_remove:
            self.unsubscribe(sub_id)
    
    def emit(self, event: BaseEvent) -> None:
        """发送事件到队列（用于异步处理）"""
        self._event_queue.put_nowait(event)
    
    async def start(self) -> None:
        """启动事件处理循环"""
        if self._running:
            return
        
        self._running = True
        self._worker_task = asyncio.create_task(self._event_loop())
        logger.info(f"[EventBus:{self.name}] 事件循环已启动")
    
    async def stop(self) -> None:
        """停止事件处理循环"""
        self._running = False
        
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None
        
        logger.info(f"[EventBus:{self.name}] 事件循环已停止")
    
    async def _event_loop(self) -> None:
        """事件处理循环"""
        while self._running:
            try:
                event = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=1.0
                )
                await self.publish_async(event)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[EventBus:{self.name}] 事件循环错误: {e}")
    
    def clear(self) -> None:
        """清空所有订阅"""
        self._subscriptions.clear()
        self._type_index.clear()
        self._global_subscriptions.clear()
        logger.info(f"[EventBus:{self.name}] 已清空所有订阅")


# 全局事件总线
_global_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """获取全局事件总线"""
    global _global_bus
    if _global_bus is None:
        _global_bus = EventBus("global")
    return _global_bus


def set_event_bus(bus: EventBus) -> None:
    """设置全局事件总线"""
    global _global_bus
    _global_bus = bus


class TaskEventBus(EventBus):
    """任务级事件总线"""
    
    def __init__(self, task_id: str):
        super().__init__(f"task_{task_id}")
        self.task_id = task_id
    
    def publish(self, event: BaseEvent) -> None:
        """发布事件，自动添加任务 ID"""
        if hasattr(event, "task_id") and not event.task_id:
            event.task_id = self.task_id
        super().publish(event)

