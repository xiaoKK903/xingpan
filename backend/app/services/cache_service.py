import logging
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Any, Dict
from functools import wraps
import threading

logger = logging.getLogger(__name__)


class MemoryCache:
    """内存缓存实现，作为 Redis 不可用时的备选方案"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 1800):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._lock = threading.RLock()
    
    def _generate_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        key_data = {"args": args, "kwargs": kwargs, "timestamp": datetime.now().strftime("%Y-%m-%d")}
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            if key not in self._cache:
                return None
            
            item = self._cache[key]
            expire_at = item.get("expire_at")
            
            if expire_at and datetime.now() > expire_at:
                del self._cache[key]
                return None
            
            return item.get("data")
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        with self._lock:
            if len(self._cache) >= self._max_size:
                self._cleanup_oldest()
            
            expire_seconds = ttl if ttl is not None else self._default_ttl
            expire_at = datetime.now() + timedelta(seconds=expire_seconds)
            
            self._cache[key] = {
                "data": value,
                "expire_at": expire_at,
                "created_at": datetime.now()
            }
            
            return True
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self, pattern: Optional[str] = None) -> int:
        """清除缓存，支持模式匹配"""
        with self._lock:
            if pattern:
                keys_to_delete = [k for k in self._cache if pattern in k]
                for k in keys_to_delete:
                    del self._cache[k]
                return len(keys_to_delete)
            else:
                count = len(self._cache)
                self._cache.clear()
                return count
    
    def _cleanup_oldest(self) -> int:
        """清理最旧的缓存项"""
        if not self._cache:
            return 0
        
        sorted_items = sorted(
            self._cache.items(),
            key=lambda x: x[1].get("created_at", datetime.min)
        )
        
        remove_count = max(1, int(self._max_size * 0.1))
        for key, _ in sorted_items[:remove_count]:
            del self._cache[key]
        
        return remove_count
    
    def get_ttl(self, key: str) -> int:
        """获取剩余过期时间（秒）"""
        with self._lock:
            if key not in self._cache:
                return -2
            
            item = self._cache[key]
            expire_at = item.get("expire_at")
            
            if expire_at is None:
                return -1
            
            remaining = (expire_at - datetime.now()).total_seconds()
            return max(0, int(remaining))


class CacheService:
    """内存缓存服务（适用于本地开发和轻量场景）
    
    注意: 生产环境建议使用 app.redis_client 中的异步 RedisManager 实现缓存。
    本服务仅提供进程内内存缓存，重启后数据丢失。
    """
    
    _instance = None
    _lock = threading.RLock()
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, default_ttl: int = 1800):
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self._default_ttl = default_ttl
        self._memory_cache = MemoryCache(max_size=2000, default_ttl=default_ttl)
        self._initialized = True
    
    def get(self, key: str) -> Optional[Any]:
        return self._memory_cache.get(key)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        effective_ttl = ttl if ttl is not None else self._default_ttl
        return self._memory_cache.set(key, value, effective_ttl)
    
    def delete(self, key: str) -> bool:
        return self._memory_cache.delete(key)
    
    def clear(self, pattern: Optional[str] = None) -> int:
        return self._memory_cache.clear(pattern)
    
    def get_ttl(self, key: str) -> int:
        return self._memory_cache.get_ttl(key)
    
    def cached(self, prefix: str = "cache", ttl: Optional[int] = None):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                cache_key = self._generate_key(prefix, func.__name__, args, kwargs)
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"缓存命中: {prefix}:{func.__name__}")
                    return cached_result
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl)
                logger.debug(f"缓存已设置: {prefix}:{func.__name__}")
                return result
            return wrapper
        return decorator
    
    def async_cached(self, prefix: str = "cache", ttl: Optional[int] = None):
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                cache_key = self._generate_key(prefix, func.__name__, args, kwargs)
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"缓存命中: {prefix}:{func.__name__}")
                    return cached_result
                result = await func(*args, **kwargs)
                self.set(cache_key, result, ttl)
                logger.debug(f"缓存已设置: {prefix}:{func.__name__}")
                return result
            return wrapper
        return decorator
    
    def _generate_key(self, prefix: str, func_name: str, args: tuple, kwargs: dict) -> str:
        key_data = {
            "func": func_name,
            "args": self._serialize_args(args),
            "kwargs": self._serialize_args(kwargs)
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    def _serialize_args(self, obj) -> Any:
        if hasattr(obj, '__dict__'):
            return {k: self._serialize_args(v) for k, v in obj.__dict__.items()
                    if not k.startswith('_')}
        elif isinstance(obj, dict):
            return {k: self._serialize_args(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._serialize_args(item) for item in obj]
        else:
            return obj


cache_service = CacheService(default_ttl=1800)


def get_cache_service() -> CacheService:
    """获取缓存服务单例"""
    return cache_service
