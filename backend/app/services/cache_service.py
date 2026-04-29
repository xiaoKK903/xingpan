import logging
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Any, Dict
from functools import wraps
import threading

from app.config import settings

logger = logging.getLogger(__name__)

REDIS_AVAILABLE = False
redis_client = None

try:
    import redis
    REDIS_AVAILABLE = True
    logger.info("Redis 库已加载")
except ImportError:
    logger.warning("Redis 库未安装，将使用内存缓存作为备选方案")


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


class RedisCache:
    """Redis 缓存实现"""
    
    def __init__(self, redis_url: Optional[str] = None, default_ttl: int = 1800):
        self._default_ttl = default_ttl
        self._client: Optional[redis.Redis] = None
        self._redis_url = redis_url or getattr(settings, "REDIS_URL", None) or "redis://localhost:6379/0"
        self._connect()
    
    def _connect(self):
        """连接到 Redis"""
        global REDIS_AVAILABLE, redis_client
        
        if not REDIS_AVAILABLE:
            return
        
        try:
            import redis
            self._client = redis.from_url(
                self._redis_url,
                decode_responses=False,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            self._client.ping()
            redis_client = self._client
            logger.info(f"成功连接到 Redis: {self._redis_url}")
        except Exception as e:
            logger.warning(f"Redis 连接失败，将使用内存缓存: {e}")
            self._client = None
    
    def _is_connected(self) -> bool:
        """检查是否已连接"""
        if self._client is None:
            return False
        try:
            self._client.ping()
            return True
        except Exception:
            return False
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """生成缓存键"""
        key_data = {"args": args, "kwargs": kwargs}
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if not self._is_connected():
            return None
        
        try:
            data = self._client.get(key)
            if data is None:
                return None
            
            return json.loads(data)
        except Exception as e:
            logger.warning(f"Redis get 失败: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        if not self._is_connected():
            return False
        
        try:
            expire_seconds = ttl if ttl is not None else self._default_ttl
            data = json.dumps(value, ensure_ascii=False, default=str)
            
            if expire_seconds > 0:
                self._client.setex(key, expire_seconds, data)
            else:
                self._client.set(key, data)
            
            return True
        except Exception as e:
            logger.warning(f"Redis set 失败: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self._is_connected():
            return False
        
        try:
            result = self._client.delete(key)
            return result > 0
        except Exception as e:
            logger.warning(f"Redis delete 失败: {e}")
            return False
    
    def clear(self, pattern: Optional[str] = None) -> int:
        """清除缓存"""
        if not self._is_connected():
            return 0
        
        try:
            if pattern:
                keys = self._client.keys(pattern)
                if keys:
                    return self._client.delete(*keys)
                return 0
            else:
                return self._client.flushdb()
        except Exception as e:
            logger.warning(f"Redis clear 失败: {e}")
            return 0
    
    def get_ttl(self, key: str) -> int:
        """获取剩余过期时间"""
        if not self._is_connected():
            return -2
        
        try:
            return self._client.ttl(key)
        except Exception as e:
            logger.warning(f"Redis ttl 失败: {e}")
            return -2


class CacheService:
    """统一缓存服务，自动选择 Redis 或内存缓存"""
    
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
        self._redis_cache: Optional[RedisCache] = None
        self._memory_cache = MemoryCache(max_size=2000, default_ttl=default_ttl)
        self._use_redis = False
        
        self._init_redis()
        self._initialized = True
    
    def _init_redis(self):
        """初始化 Redis 缓存"""
        global REDIS_AVAILABLE
        
        if not REDIS_AVAILABLE:
            logger.info("Redis 未安装，使用内存缓存")
            return
        
        try:
            self._redis_cache = RedisCache(default_ttl=self._default_ttl)
            if self._redis_cache._is_connected():
                self._use_redis = True
                logger.info("缓存服务已使用 Redis")
            else:
                logger.warning("Redis 连接失败，切换到内存缓存")
                self._use_redis = False
        except Exception as e:
            logger.warning(f"Redis 初始化失败，使用内存缓存: {e}")
            self._use_redis = False
    
    def _get_cache(self):
        """获取当前使用的缓存实例"""
        if self._use_redis and self._redis_cache:
            return self._redis_cache
        return self._memory_cache
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        cache = self._get_cache()
        return cache.get(key)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        effective_ttl = ttl if ttl is not None else self._default_ttl
        cache = self._get_cache()
        return cache.set(key, value, effective_ttl)
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        cache = self._get_cache()
        return cache.delete(key)
    
    def clear(self, pattern: Optional[str] = None) -> int:
        """清除缓存"""
        cache = self._get_cache()
        return cache.clear(pattern)
    
    def get_ttl(self, key: str) -> int:
        """获取剩余过期时间（秒）
        返回 -2 表示键不存在，-1 表示永不过期
        """
        cache = self._get_cache()
        return cache.get_ttl(key)
    
    def cached(self, prefix: str = "cache", ttl: Optional[int] = None):
        """装饰器：缓存函数结果"""
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
        """装饰器：缓存异步函数结果"""
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
        """生成缓存键"""
        key_data = {
            "func": func_name,
            "args": self._serialize_args(args),
            "kwargs": self._serialize_args(kwargs)
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    def _serialize_args(self, obj) -> Any:
        """序列化参数，用于生成缓存键"""
        if hasattr(obj, '__dict__'):
            return {k: self._serialize_args(v) for k, v in obj.__dict__.items() 
                    if not k.startswith('_')}
        elif isinstance(obj, dict):
            return {k: self._serialize_args(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._serialize_args(item) for item in obj]
        else:
            return obj
    
    @property
    def is_using_redis(self) -> bool:
        """检查是否正在使用 Redis"""
        return self._use_redis


cache_service = CacheService(default_ttl=1800)


def get_cache_service() -> CacheService:
    """获取缓存服务单例"""
    return cache_service
