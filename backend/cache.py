"""Redis cache management."""
from typing import Optional, Any
import json

try:
    import redis.asyncio as redis
    from redis.asyncio import Redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    Redis = None
    redis = None

from .config import settings

# Global Redis connection pool
_redis_pool: Optional[Redis] = None


async def get_redis() -> Optional[Redis]:
    """
    Get Redis connection.
    
    Returns:
        Redis: Redis connection instance or None if Redis not available
    """
    if not HAS_REDIS:
        return None
    
    global _redis_pool
    if _redis_pool is None:
        try:
            if settings.REDIS_URL:
                _redis_pool = await redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True
                )
            else:
                _redis_pool = await redis.from_pool(
                    redis.ConnectionPool(
                        host=settings.REDIS_HOST,
                        port=settings.REDIS_PORT,
                        db=settings.REDIS_DB,
                        password=settings.REDIS_PASSWORD,
                        encoding="utf-8",
                        decode_responses=True
                    )
                )
        except Exception:
            return None
    return _redis_pool


async def close_redis() -> None:
    """Close Redis connection."""
    global _redis_pool
    if _redis_pool:
        await _redis_pool.close()
        _redis_pool = None


async def get_cache(key: str) -> Optional[Any]:
    """
    Get value from cache.
    
    Args:
        key: Cache key
        
    Returns:
        Cached value or None
    """
    if not HAS_REDIS:
        return None
    try:
        redis_client = await get_redis()
        if not redis_client:
            return None
        value = await redis_client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception:
        return None


async def set_cache(key: str, value: Any, expire: Optional[int] = None) -> bool:
    """
    Set value in cache.
    
    Args:
        key: Cache key
        value: Value to cache
        expire: Expiration time in seconds
        
    Returns:
        True if successful, False otherwise
    """
    if not HAS_REDIS:
        return False
    try:
        redis_client = await get_redis()
        if not redis_client:
            return False
        serialized = json.dumps(value, default=str)
        if expire:
            await redis_client.setex(key, expire, serialized)
        else:
            await redis_client.set(key, serialized)
        return True
    except Exception:
        return False


async def delete_cache(key: str) -> bool:
    """
    Delete value from cache.
    
    Args:
        key: Cache key
        
    Returns:
        True if successful, False otherwise
    """
    if not HAS_REDIS:
        return False
    try:
        redis_client = await get_redis()
        if not redis_client:
            return False
        await redis_client.delete(key)
        return True
    except Exception:
        return False


async def clear_cache_pattern(pattern: str) -> int:
    """
    Clear cache keys matching pattern.
    
    Args:
        pattern: Redis key pattern (e.g., "drone:*")
        
    Returns:
        Number of keys deleted
    """
    if not HAS_REDIS:
        return 0
    try:
        redis_client = await get_redis()
        if not redis_client:
            return 0
        keys = await redis_client.keys(pattern)
        if keys:
            return await redis_client.delete(*keys)
        return 0
    except Exception:
        return 0

