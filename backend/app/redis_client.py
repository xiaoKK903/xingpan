import logging
import json
from typing import Optional, Any, Dict
from datetime import datetime
import redis.asyncio as redis
from app.config import settings

logger = logging.getLogger(__name__)


class RedisManager:
    """
    Redis 连接管理器
    
    职责：
    - 管理 Redis 连接池
    - 提供缓存、获取、删除等基础操作
    - 支持 JSON 序列化/反序列化
    """
    
    _instance: Optional['RedisManager'] = None
    _redis: Optional[redis.Redis] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def initialize(self):
        """初始化 Redis 连接"""
        if self._redis is not None:
            return
        
        if not settings.REDIS_URL:
            try:
                self._redis = redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=False
                )
                logger.info("Redis 连接已初始化")
            except Exception as e:
                logger.warning(f"Redis 连接失败: {e}，将使用内存缓存替代")
                self._redis = None
        else:
            logger.info("未配置 REDIS_URL，将使用内存缓存替代")
            self._redis = None
    
    def get_client(self) -> Optional[redis.Redis]:
        """获取 Redis 客户端"""
        return self._redis
    
    async def close(self):
        """关闭 Redis 连接"""
        if self._redis is not None:
            await self._redis.close()
            self._redis = None
            logger.info("Redis 连接已关闭")
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ):
        """设置缓存值"""
        if self._redis is None:
            return
        
        try:
            serialized = json.dumps(value, ensure_ascii=False, default=str)
            if ttl:
                await self._redis.setex(key, ttl, serialized)
            else:
                await self._redis.set(key, serialized)
        except Exception as e:
            logger.error(f"Redis set 失败: {e}")
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if self._redis is None:
            return None
        
        try:
            data = await self._redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Redis get 失败: {e}")
            return None
    
    async def delete(self, key: str):
        """删除缓存键"""
        if self._redis is None:
            return
        
        try:
            await self._redis.delete(key)
        except Exception as e:
            logger.error(f"Redis delete 失败: {e}")
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if self._redis is None:
            return False
        
        try:
            return await self._redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis exists 失败: {e}")
            return False
    
    async def expire(self, key: str, ttl: int):
        """设置过期时间"""
        if self._redis is None:
            return
        
        try:
            await self._redis.expire(key, ttl)
        except Exception as e:
            logger.error(f"Redis expire 失败: {e}")
    
    async def hash_increment(
        self,
        key: str,
        field: str,
        amount: int = 1
    ) -> int:
        """Hash 字段增量"""
        if self._redis is None:
            return 0
        
        try:
            return await self._redis.hincrby(key, field, amount)
        except Exception as e:
            logger.error(f"Redis hash_increment 失败: {e}")
            return 0
    
    async def hash_get(self, key: str, field: str) -> Optional[Any]:
        """获取 Hash 字段值"""
        if self._redis is None:
            return None
        
        try:
            data = await self._redis.hget(key, field)
            if data:
                return json.loads(data) if isinstance(data, bytes) else data
            return None
        except Exception as e:
            logger.error(f"Redis hash_get 失败: {e}")
            return None
    
    async def hash_getall(self, key: str) -> Dict[str, Any]:
        """获取 Hash 所有字段"""
        if self._redis is None:
            return {}
        
        try:
            data = await self._redis.hgetall(key)
            result = {}
            for k, v in data.items():
                if isinstance(k, bytes):
                    k = k.decode('utf-8')
                if isinstance(v, bytes):
                    v = v.decode('utf-8')
                try:
                    result[k] = json.loads(v)
                except:
                    result[k] = v
            return result
        except Exception as e:
            logger.error(f"Redis hash_getall 失败: {e}")
            return {}
    
    async def hash_set(
        self,
        key: str,
        field: str,
        value: Any
    ):
        """设置 Hash 字段值"""
        if self._redis is None:
            return
        
        try:
            serialized = json.dumps(value, ensure_ascii=False, default=str)
            await self._redis.hset(key, field, serialized)
        except Exception as e:
            logger.error(f"Redis hash_set 失败: {e}")
    
    async def sorted_set_add(
        self,
        key: str,
        member: str,
        score: float
    ):
        """添加到有序集合"""
        if self._redis is None:
            return
        
        try:
            await self._redis.zadd(key, {member: score})
        except Exception as e:
            logger.error(f"Redis sorted_set_add 失败: {e}")
    
    async def sorted_set_range(
        self,
        key: str,
        start: int = 0,
        end: int = -1,
        desc: bool = True
    ) -> list:
        """获取有序集合范围"""
        if self._redis is None:
            return []
        
        try:
            if desc:
                return await self._redis.zrevrange(key, start, end, withscores=True)
            return await self._redis.zrange(key, start, end, withscores=True)
        except Exception as e:
            logger.error(f"Redis sorted_set_range 失败: {e}")
            return []
    
    async def sorted_set_remove(
        self,
        key: str,
        members: list
    ):
        """从有序集合移除成员"""
        if self._redis is None:
            return
        
        try:
            await self._redis.zrem(key, *members)
        except Exception as e:
            logger.error(f"Redis sorted_set_remove 失败: {e}")
    
    async def publish(self, channel: str, message: Any):
        """发布消息到频道"""
        if self._redis is None:
            return
        
        try:
            serialized = json.dumps(message, ensure_ascii=False, default=str)
            await self._redis.publish(channel, serialized)
        except Exception as e:
            logger.error(f"Redis publish 失败: {e}")


redis_manager = RedisManager()


async def get_redis_manager() -> RedisManager:
    """获取 Redis 管理器单例"""
    if redis_manager.get_client() is None:
        await redis_manager.initialize()
    return redis_manager
