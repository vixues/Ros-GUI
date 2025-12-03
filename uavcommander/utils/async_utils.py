"""
异步工具模块

提供异步编程的辅助工具。
"""

import asyncio
from typing import (
    Optional,
    Dict,
    List,
    Any,
    Callable,
    Awaitable,
    TypeVar,
    Generic,
    Union,
    Tuple,
)
from dataclasses import dataclass
from datetime import datetime, timedelta
import functools
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

T = TypeVar("T")


class AsyncTimeout:
    """异步超时上下文管理器"""
    
    def __init__(self, seconds: float, message: str = "操作超时"):
        self.seconds = seconds
        self.message = message
        self._task: Optional[asyncio.Task] = None
    
    async def __aenter__(self) -> "AsyncTimeout":
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        return False
    
    async def run(self, coro: Awaitable[T]) -> T:
        """运行协程，带超时控制"""
        try:
            return await asyncio.wait_for(coro, timeout=self.seconds)
        except asyncio.TimeoutError:
            raise TimeoutError(self.message)


async def wait_with_timeout(
    coro: Awaitable[T],
    timeout: float,
    default: Optional[T] = None,
) -> Tuple[bool, Optional[T]]:
    """
    带超时的等待
    
    Returns:
        (success, result) - 成功标志和结果
    """
    try:
        result = await asyncio.wait_for(coro, timeout=timeout)
        return True, result
    except asyncio.TimeoutError:
        return False, default


class RetryConfig:
    """重试配置"""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_backoff: bool = True,
        jitter: bool = True,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_backoff = exponential_backoff
        self.jitter = jitter
    
    def get_delay(self, attempt: int) -> float:
        """计算重试延迟"""
        if self.exponential_backoff:
            delay = self.base_delay * (2 ** attempt)
        else:
            delay = self.base_delay
        
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            import random
            delay *= (0.5 + random.random())
        
        return delay


async def retry_async(
    func: Callable[..., Awaitable[T]],
    *args,
    config: Optional[RetryConfig] = None,
    retry_exceptions: Tuple[type, ...] = (Exception,),
    **kwargs,
) -> T:
    """
    异步重试执行
    
    Args:
        func: 要执行的异步函数
        *args: 位置参数
        config: 重试配置
        retry_exceptions: 需要重试的异常类型
        **kwargs: 关键字参数
    
    Returns:
        函数执行结果
    
    Raises:
        最后一次执行的异常
    """
    config = config or RetryConfig()
    last_exception = None
    
    for attempt in range(config.max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except retry_exceptions as e:
            last_exception = e
            
            if attempt < config.max_retries:
                delay = config.get_delay(attempt)
                logger.warning(
                    f"重试 {attempt + 1}/{config.max_retries}: "
                    f"{type(e).__name__}: {e}, 等待 {delay:.2f}s"
                )
                await asyncio.sleep(delay)
            else:
                logger.error(f"重试耗尽: {type(e).__name__}: {e}")
    
    raise last_exception


def async_retry(
    config: Optional[RetryConfig] = None,
    retry_exceptions: Tuple[type, ...] = (Exception,),
):
    """重试装饰器"""
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await retry_async(
                func, *args,
                config=config,
                retry_exceptions=retry_exceptions,
                **kwargs
            )
        return wrapper
    return decorator


class AsyncLock:
    """增强的异步锁"""
    
    def __init__(self, name: str = ""):
        self.name = name
        self._lock = asyncio.Lock()
        self._owner: Optional[str] = None
        self._acquired_at: Optional[datetime] = None
    
    async def acquire(self, owner: str = "") -> bool:
        await self._lock.acquire()
        self._owner = owner
        self._acquired_at = datetime.now()
        return True
    
    def release(self) -> None:
        self._owner = None
        self._acquired_at = None
        self._lock.release()
    
    async def __aenter__(self) -> "AsyncLock":
        await self.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release()
    
    @property
    def locked(self) -> bool:
        return self._lock.locked()
    
    @property
    def hold_time(self) -> Optional[timedelta]:
        if self._acquired_at:
            return datetime.now() - self._acquired_at
        return None


class AsyncSemaphore:
    """增强的信号量"""
    
    def __init__(self, value: int, name: str = ""):
        self.name = name
        self._semaphore = asyncio.Semaphore(value)
        self._max_value = value
        self._current = value
    
    async def acquire(self) -> bool:
        await self._semaphore.acquire()
        self._current -= 1
        return True
    
    def release(self) -> None:
        self._current += 1
        self._semaphore.release()
    
    async def __aenter__(self) -> "AsyncSemaphore":
        await self.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release()
    
    @property
    def available(self) -> int:
        return self._current


class AsyncQueue(Generic[T]):
    """增强的异步队列"""
    
    def __init__(self, maxsize: int = 0, name: str = ""):
        self.name = name
        self._queue: asyncio.Queue[T] = asyncio.Queue(maxsize)
        self._total_put = 0
        self._total_get = 0
    
    async def put(self, item: T, timeout: Optional[float] = None) -> None:
        if timeout:
            await asyncio.wait_for(self._queue.put(item), timeout)
        else:
            await self._queue.put(item)
        self._total_put += 1
    
    def put_nowait(self, item: T) -> None:
        self._queue.put_nowait(item)
        self._total_put += 1
    
    async def get(self, timeout: Optional[float] = None) -> T:
        if timeout:
            item = await asyncio.wait_for(self._queue.get(), timeout)
        else:
            item = await self._queue.get()
        self._total_get += 1
        return item
    
    def get_nowait(self) -> T:
        item = self._queue.get_nowait()
        self._total_get += 1
        return item
    
    @property
    def size(self) -> int:
        return self._queue.qsize()
    
    @property
    def empty(self) -> bool:
        return self._queue.empty()
    
    @property
    def full(self) -> bool:
        return self._queue.full()
    
    @property
    def stats(self) -> Dict[str, int]:
        return {
            "size": self.size,
            "total_put": self._total_put,
            "total_get": self._total_get,
        }


class TaskGroup:
    """任务组管理"""
    
    def __init__(self, name: str = ""):
        self.name = name
        self._tasks: Dict[str, asyncio.Task] = {}
        self._results: Dict[str, Any] = {}
        self._errors: Dict[str, Exception] = {}
    
    def add(self, name: str, coro: Awaitable[Any]) -> asyncio.Task:
        """添加任务"""
        task = asyncio.create_task(coro)
        self._tasks[name] = task
        return task
    
    async def wait_all(
        self,
        timeout: Optional[float] = None,
        return_when: str = asyncio.ALL_COMPLETED,
    ) -> Tuple[Dict[str, Any], Dict[str, Exception]]:
        """等待所有任务完成"""
        if not self._tasks:
            return {}, {}
        
        done, pending = await asyncio.wait(
            list(self._tasks.values()),
            timeout=timeout,
            return_when=return_when,
        )
        
        for name, task in self._tasks.items():
            if task in done:
                try:
                    self._results[name] = task.result()
                except Exception as e:
                    self._errors[name] = e
        
        # 取消未完成的任务
        for task in pending:
            task.cancel()
        
        return self._results, self._errors
    
    async def cancel_all(self) -> None:
        """取消所有任务"""
        for task in self._tasks.values():
            if not task.done():
                task.cancel()
        
        await asyncio.gather(*self._tasks.values(), return_exceptions=True)


@asynccontextmanager
async def cancellation_scope(timeout: Optional[float] = None):
    """可取消的作用域"""
    cancel_event = asyncio.Event()
    
    async def cancellable():
        if timeout:
            await asyncio.sleep(timeout)
            cancel_event.set()
    
    timeout_task = None
    if timeout:
        timeout_task = asyncio.create_task(cancellable())
    
    try:
        yield cancel_event
    finally:
        if timeout_task and not timeout_task.done():
            timeout_task.cancel()
            try:
                await timeout_task
            except asyncio.CancelledError:
                pass


async def gather_with_concurrency(
    limit: int,
    *coros: Awaitable[T],
) -> List[T]:
    """带并发限制的 gather"""
    semaphore = asyncio.Semaphore(limit)
    
    async def limited_coro(coro: Awaitable[T]) -> T:
        async with semaphore:
            return await coro
    
    return await asyncio.gather(*[limited_coro(c) for c in coros])


def run_sync(coro: Awaitable[T]) -> T:
    """在同步环境中运行异步函数"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    if loop.is_running():
        # 如果事件循环已在运行，创建新线程执行
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()
    else:
        return loop.run_until_complete(coro)

