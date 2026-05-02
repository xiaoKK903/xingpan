import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models import OnlineUserPresence, Chart, User
from app.redis_client import redis_manager, get_redis_manager

logger = logging.getLogger(__name__)

MAIN_PLANETS = [
    "太阳", "月亮", "水星", "金星", "火星",
    "木星", "土星", "天王星", "海王星", "冥王星"
]

ZODIAC_SIGNS = [
    "白羊座", "金牛座", "双子座", "巨蟹座", "狮子座", "处女座",
    "天秤座", "天蝎座", "射手座", "摩羯座", "水瓶座", "双鱼座"
]

BUCKET_SIZE = 10
ZODIAC_DEGREES = 360
NUM_BUCKETS = ZODIAC_DEGREES // BUCKET_SIZE


class OnlineUserCacheService:
    """
    在线用户缓存服务
    
    职责：
    - 管理在线用户的 Redis 缓存
    - 实现黄道 360° 区间桶计数增量聚合
    - 避免全量遍历重算，提升性能
    """
    
    def __init__(self):
        self._online_timeout_seconds = 30 * 60
    
    def _get_online_users_key(self, scope: str = "global", city: Optional[str] = None) -> str:
        """获取在线用户集合的 Redis 键"""
        if scope == "local" and city:
            return f"energy:online_users:local:{city}"
        return f"energy:online_users:global"
    
    def _get_user_presence_key(self, user_id: int) -> str:
        """获取用户状态的 Redis 键"""
        return f"energy:user_presence:{user_id}"
    
    def _get_planet_bucket_key(self, planet: str, scope: str = "global", city: Optional[str] = None) -> str:
        """获取行星区间桶的 Redis 键"""
        if scope == "local" and city:
            return f"energy:planet_buckets:{planet}:local:{city}"
        return f"energy:planet_buckets:{planet}:global"
    
    def _get_energy_cache_key(self, scope: str = "global", city: Optional[str] = None) -> str:
        """获取能量快照缓存的 Redis 键"""
        if scope == "local" and city:
            return f"energy:cache:snapshot:local:{city}"
        return f"energy:cache:snapshot:global"
    
    def _degree_to_bucket(self, longitude: float) -> int:
        """将黄经转换为区间桶索引"""
        normalized = longitude % ZODIAC_DEGREES
        return int(normalized // BUCKET_SIZE)
    
    def _bucket_to_degree_range(self, bucket: int) -> tuple:
        """将区间桶索引转换为度数范围"""
        start = bucket * BUCKET_SIZE
        end = (bucket + 1) * BUCKET_SIZE
        return start, end
    
    async def update_user_online(
        self,
        db: Session,
        user_id: int,
        session_id: Optional[str] = None,
        city: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        chart_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        更新用户在线状态（Redis + 数据库双写）
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            session_id: 会话ID
            city: 城市
            latitude: 纬度
            longitude: 经度
            chart_id: 星盘ID
            
        Returns:
            用户状态数据
        """
        redis_mgr = await get_redis_manager()
        now = datetime.utcnow()
        
        chart_data = None
        if chart_id:
            chart = db.query(Chart).filter(Chart.id == chart_id).first()
            if chart and chart.chart_data:
                chart_data = json.loads(chart.chart_data)
        
        user = db.query(User).filter(User.id == user_id).first()
        
        presence_data = {
            "user_id": user_id,
            "username": user.username if user else None,
            "session_id": session_id,
            "city": city,
            "latitude": latitude,
            "longitude": longitude,
            "chart_id": chart_id,
            "chart_data": chart_data,
            "last_seen_at": now.isoformat(),
            "is_online": True
        }
        
        await redis_mgr.set(
            self._get_user_presence_key(user_id),
            presence_data,
            self._online_timeout_seconds
        )
        
        global_key = self._get_online_users_key("global")
        await redis_mgr.sorted_set_add(global_key, str(user_id), now.timestamp())
        await redis_mgr.expire(global_key, self._online_timeout_seconds)
        
        if city:
            local_key = self._get_online_users_key("local", city)
            await redis_mgr.sorted_set_add(local_key, str(user_id), now.timestamp())
            await redis_mgr.expire(local_key, self._online_timeout_seconds)
        
        if chart_data:
            await self._update_planet_buckets(user_id, chart_data, "global")
            if city:
                await self._update_planet_buckets(user_id, chart_data, "local", city)
        
        existing = db.query(OnlineUserPresence).filter(
            OnlineUserPresence.user_id == user_id
        ).first()
        
        if existing:
            existing.is_online = True
            existing.last_seen_at = now
            if session_id:
                existing.session_id = session_id
            if city:
                existing.last_city = city
            if latitude is not None:
                existing.last_latitude = latitude
            if longitude is not None:
                existing.last_longitude = longitude
            if chart_id:
                existing.primary_chart_id = chart_id
            existing.updated_at = now
            db.commit()
            db.refresh(existing)
        else:
            presence = OnlineUserPresence(
                user_id=user_id,
                session_id=session_id,
                last_city=city,
                last_latitude=latitude,
                last_longitude=longitude,
                primary_chart_id=chart_id,
                is_online=True,
                last_seen_at=now,
                created_at=now,
                updated_at=now
            )
            db.add(presence)
            db.commit()
        
        return presence_data
    
    async def _update_planet_buckets(
        self,
        user_id: int,
        chart_data: Dict[str, Any],
        scope: str = "global",
        city: Optional[str] = None
    ):
        """
        更新行星区间桶计数
        
        每个行星的黄经分布在 360° 黄道上，
        按 BUCKET_SIZE 间隔划分区间桶，
        使用 Redis Hash 存储各桶的用户计数。
        """
        redis_mgr = await get_redis_manager()
        
        planets = chart_data.get("planets", [])
        if not planets:
            return
        
        for planet in planets:
            planet_name = planet.get("name")
            if planet_name not in MAIN_PLANETS:
                continue
            
            longitude = planet.get("longitude", 0.0)
            bucket = self._degree_to_bucket(longitude)
            
            bucket_key = self._get_planet_bucket_key(planet_name, scope, city)
            
            user_bucket_key = f"{bucket_key}:users"
            users_in_bucket = await redis_mgr.hash_get(user_bucket_key, str(bucket)) or []
            
            if str(user_id) not in users_in_bucket:
                users_in_bucket.append(str(user_id))
                await redis_mgr.hash_set(user_bucket_key, str(bucket), users_in_bucket)
                
                await redis_mgr.hash_increment(bucket_key, str(bucket), 1)
        
        await redis_mgr.expire(self._get_planet_bucket_key("太阳", scope, city), self._online_timeout_seconds)
    
    async def mark_user_offline(self, db: Session, user_id: int) -> bool:
        """
        标记用户为离线
        """
        redis_mgr = await get_redis_manager()
        
        presence = await redis_mgr.get(self._get_user_presence_key(user_id))
        city = presence.get("city") if presence else None
        chart_data = presence.get("chart_data") if presence else None
        
        if chart_data:
            await self._remove_user_from_buckets(user_id, chart_data, "global")
            if city:
                await self._remove_user_from_buckets(user_id, chart_data, "local", city)
        
        await redis_mgr.delete(self._get_user_presence_key(user_id))
        
        global_key = self._get_online_users_key("global")
        await redis_mgr.sorted_set_remove(global_key, [str(user_id)])
        
        if city:
            local_key = self._get_online_users_key("local", city)
            await redis_mgr.sorted_set_remove(local_key, [str(user_id)])
        
        db_presence = db.query(OnlineUserPresence).filter(
            OnlineUserPresence.user_id == user_id
        ).first()
        
        if db_presence:
            db_presence.is_online = False
            db_presence.updated_at = datetime.utcnow()
            db.commit()
            return True
        
        return False
    
    async def _remove_user_from_buckets(
        self,
        user_id: int,
        chart_data: Dict[str, Any],
        scope: str = "global",
        city: Optional[str] = None
    ):
        """从行星区间桶中移除用户"""
        redis_mgr = await get_redis_manager()
        
        planets = chart_data.get("planets", [])
        if not planets:
            return
        
        for planet in planets:
            planet_name = planet.get("name")
            if planet_name not in MAIN_PLANETS:
                continue
            
            longitude = planet.get("longitude", 0.0)
            bucket = self._degree_to_bucket(longitude)
            
            bucket_key = self._get_planet_bucket_key(planet_name, scope, city)
            user_bucket_key = f"{bucket_key}:users"
            
            users_in_bucket = await redis_mgr.hash_get(user_bucket_key, str(bucket)) or []
            
            if str(user_id) in users_in_bucket:
                users_in_bucket.remove(str(user_id))
                await redis_mgr.hash_set(user_bucket_key, str(bucket), users_in_bucket)
                
                await redis_mgr.hash_increment(bucket_key, str(bucket), -1)
    
    async def get_online_count(
        self,
        scope: str = "global",
        city: Optional[str] = None
    ) -> int:
        """获取在线用户数量（从 Redis 缓存）"""
        redis_mgr = await get_redis_manager()
        
        key = self._get_online_users_key(scope, city)
        members = await redis_mgr.sorted_set_range(key, 0, -1, desc=False)
        
        now = datetime.utcnow().timestamp()
        cutoff = now - self._online_timeout_seconds
        
        count = 0
        for member, score in members:
            if isinstance(member, bytes):
                member = member.decode('utf-8')
            if score >= cutoff:
                count += 1
        
        return count
    
    async def get_online_users(
        self,
        scope: str = "global",
        city: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取在线用户列表（从 Redis 缓存）"""
        redis_mgr = await get_redis_manager()
        
        key = self._get_online_users_key(scope, city)
        members = await redis_mgr.sorted_set_range(key, 0, limit - 1, desc=True)
        
        now = datetime.utcnow().timestamp()
        cutoff = now - self._online_timeout_seconds
        
        users = []
        for member, score in members:
            if isinstance(member, bytes):
                member = member.decode('utf-8')
            if score >= cutoff:
                try:
                    user_id = int(member)
                    presence = await redis_mgr.get(self._get_user_presence_key(user_id))
                    if presence:
                        users.append(presence)
                except ValueError:
                    continue
        
        return users
    
    async def get_planet_distribution_from_cache(
        self,
        scope: str = "global",
        city: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        从 Redis 缓存获取行星分布统计
        
        使用区间桶计数增量聚合，避免全量遍历重算
        """
        redis_mgr = await get_redis_manager()
        
        planet_distribution = {
            planet: {sign: 0 for sign in ZODIAC_SIGNS}
            for planet in MAIN_PLANETS
        }
        
        bucket_distribution = {}
        
        for planet in MAIN_PLANETS:
            bucket_key = self._get_planet_bucket_key(planet, scope, city)
            buckets = await redis_mgr.hash_getall(bucket_key)
            
            bucket_distribution[planet] = {}
            for bucket_str, count in buckets.items():
                try:
                    bucket = int(bucket_str)
                    count = int(count) if isinstance(count, str) else count
                    
                    if count > 0:
                        bucket_distribution[planet][bucket] = count
                        
                        sign_index = (bucket * BUCKET_SIZE) // 30
                        sign = ZODIAC_SIGNS[sign_index % 12]
                        planet_distribution[planet][sign] += count
                except (ValueError, TypeError):
                    continue
        
        total_users = await self.get_online_count(scope, city)
        
        dominant_planets = []
        for planet_name, sign_counts in planet_distribution.items():
            if not any(sign_counts.values()):
                continue
            
            max_count = max(sign_counts.values())
            if max_count == 0:
                continue
            
            dominant_signs = [sign for sign, count in sign_counts.items() if count == max_count]
            
            for sign in dominant_signs:
                percentage = (max_count / total_users * 100) if total_users > 0 else 0
                dominant_planets.append({
                    "planet": planet_name,
                    "dominant_sign": sign,
                    "count": max_count,
                    "percentage": round(percentage, 1)
                })
        
        dominant_planets.sort(key=lambda x: x["percentage"], reverse=True)
        
        return {
            "distribution": planet_distribution,
            "bucket_distribution": bucket_distribution,
            "dominant_planets": dominant_planets[:5],
            "total_users": total_users
        }
    
    async def cache_energy_snapshot(
        self,
        snapshot: Dict[str, Any],
        scope: str = "global",
        city: Optional[str] = None,
        ttl: int = 300
    ):
        """缓存能量快照"""
        redis_mgr = await get_redis_manager()
        
        key = self._get_energy_cache_key(scope, city)
        await redis_mgr.set(key, snapshot, ttl)
    
    async def get_cached_energy_snapshot(
        self,
        scope: str = "global",
        city: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """获取缓存的能量快照"""
        redis_mgr = await get_redis_manager()
        
        key = self._get_energy_cache_key(scope, city)
        return await redis_mgr.get(key)
    
    async def cleanup_expired_users(self):
        """清理过期的在线用户"""
        redis_mgr = await get_redis_manager()
        
        now = datetime.utcnow().timestamp()
        cutoff = now - self._online_timeout_seconds
        
        global_key = self._get_online_users_key("global")
        members = await redis_mgr.sorted_set_range(global_key, 0, -1, desc=False)
        
        expired_users = []
        for member, score in members:
            if isinstance(member, bytes):
                member = member.decode('utf-8')
            if score < cutoff:
                expired_users.append(member)
        
        if expired_users:
            await redis_mgr.sorted_set_remove(global_key, expired_users)


online_user_cache_service = OnlineUserCacheService()


async def get_online_user_cache_service() -> OnlineUserCacheService:
    """获取在线用户缓存服务单例"""
    return online_user_cache_service
