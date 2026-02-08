import json
import redis.asyncio as redis
from typing import Optional, Any, Union
from datetime import datetime, timedelta
from functools import wraps
import hashlib
import pickle

from app.core.config import get_settings

settings = get_settings()


class RedisCache:
    """Redis 缓存管理器"""
    
    def __init__(self):
        self._redis: Optional[redis.Redis] = None
        self._url = settings.REDIS_URL
        self._default_ttl = settings.REDIS_CACHE_TTL
    
    async def connect(self):
        """连接到 Redis"""
        if self._redis is None:
            self._redis = await redis.from_url(self._url, decode_responses=True)
        return self._redis
    
    async def disconnect(self):
        """断开 Redis 连接"""
        if self._redis:
            await self._redis.close()
            self._redis = None
    
    def _make_key(self, key: str, prefix: str = "dashboard") -> str:
        """生成带前缀的 key"""
        return f"{prefix}:{key}"
    
    async def get(self, key: str, prefix: str = "dashboard") -> Optional[Any]:
        """获取缓存值"""
        try:
            r = await self.connect()
            full_key = self._make_key(key, prefix)
            value = await r.get(full_key)
            
            if value is None:
                return None
            
            # 尝试 JSON 反序列化
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            print(f"Redis get error: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        prefix: str = "dashboard"
    ) -> bool:
        """设置缓存值"""
        try:
            r = await self.connect()
            full_key = self._make_key(key, prefix)
            
            # JSON 序列化
            if isinstance(value, (dict, list)):
                value = json.dumps(value, default=str)
            elif not isinstance(value, str):
                value = str(value)
            
            ttl = ttl or self._default_ttl
            await r.setex(full_key, ttl, value)
            return True
        except Exception as e:
            print(f"Redis set error: {e}")
            return False
    
    async def delete(self, key: str, prefix: str = "dashboard") -> bool:
        """删除缓存"""
        try:
            r = await self.connect()
            full_key = self._make_key(key, prefix)
            await r.delete(full_key)
            return True
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False
    
    async def delete_pattern(self, pattern: str, prefix: str = "dashboard") -> int:
        """按模式删除缓存"""
        try:
            r = await self.connect()
            full_pattern = self._make_key(pattern, prefix)
            keys = await r.keys(full_pattern)
            if keys:
                return await r.delete(*keys)
            return 0
        except Exception as e:
            print(f"Redis delete_pattern error: {e}")
            return 0
    
    async def exists(self, key: str, prefix: str = "dashboard") -> bool:
        """检查 key 是否存在"""
        try:
            r = await self.connect()
            full_key = self._make_key(key, prefix)
            return await r.exists(full_key) > 0
        except Exception as e:
            print(f"Redis exists error: {e}")
            return False
    
    async def get_or_set(
        self,
        key: str,
        callback,
        ttl: Optional[int] = None,
        prefix: str = "dashboard"
    ) -> Any:
        """获取或设置缓存"""
        # 先尝试获取
        cached = await self.get(key, prefix)
        if cached is not None:
            return cached
        
        # 执行回调获取数据
        value = await callback() if callable(callback) else callback
        
        # 设置缓存
        if value is not None:
            await self.set(key, value, ttl, prefix)
        
        return value
    
    def cache_key(self, *args, **kwargs) -> str:
        """生成缓存 key"""
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()


# 全局缓存实例
_cache_instance: Optional[RedisCache] = None


def get_cache() -> RedisCache:
    """获取全局缓存实例"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = RedisCache()
    return _cache_instance


def cached(
    ttl: Optional[int] = None,
    prefix: str = "dashboard",
    key_func: Optional[callable] = None
):
    """
    缓存装饰器
    
    Args:
        ttl: 缓存过期时间（秒）
        prefix: key 前缀
        key_func: 自定义 key 生成函数
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache()
            
            # 生成缓存 key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = cache.cache_key(
                    func.__name__,
                    *args,
                    **{k: v for k, v in kwargs.items() if k not in ['db', 'session']}
                )
            
            # 尝试获取缓存
            cached_value = await cache.get(cache_key, prefix)
            if cached_value is not None:
                return cached_value
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 设置缓存
            if result is not None:
                await cache.set(cache_key, result, ttl, prefix)
            
            return result
        return wrapper
    return decorator
