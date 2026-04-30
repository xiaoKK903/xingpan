import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models import (
    OnlineUserPresence, 
    CommunityEnergySnapshot,
    Chart,
    User
)
from app.services.energy_scoring import (
    EnergyScoringEngine, 
    Dimension, 
    DIMENSION_CONFIG,
    energy_scoring_engine
)
from app.astro import calculate_chart, parse_birth_datetime, HouseSystem

logger = logging.getLogger(__name__)

MAIN_PLANETS = [
    "太阳", "月亮", "水星", "金星", "火星",
    "木星", "土星", "天王星", "海王星", "冥王星"
]

ZODIAC_SIGNS = [
    "白羊座", "金牛座", "双子座", "巨蟹座", "狮子座", "处女座",
    "天秤座", "天蝎座", "射手座", "摩羯座", "水瓶座", "双鱼座"
]

GROUP_ASPECT_TYPES = [
    {"name": "合相", "symbol": "☌", "angle": 0.0, "orb": 10.0, "nature": "neutral"},
    {"name": "六分相", "symbol": "⚹", "angle": 60.0, "orb": 8.0, "nature": "harmonious"},
    {"name": "四分相", "symbol": "□", "angle": 90.0, "orb": 10.0, "nature": "challenging"},
    {"name": "三分相", "symbol": "△", "angle": 120.0, "orb": 10.0, "nature": "harmonious"},
    {"name": "对分相", "symbol": "☍", "angle": 180.0, "orb": 10.0, "nature": "challenging"},
]


class CommunityEnergyService:
    """
    社区能量聚合服务
    
    职责：
    - 管理在线用户状态
    - 聚合在线用户星盘数据
    - 计算行星分布、相位格局统计
    - 生成社区能量快照
    """
    
    def __init__(self):
        self._online_timeout_minutes = 30
        self._snapshot_interval_minutes = 5
    
    def update_user_presence(
        self,
        db: Session,
        user_id: int,
        session_id: Optional[str] = None,
        city: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        chart_id: Optional[int] = None
    ) -> OnlineUserPresence:
        """
        更新用户在线状态
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            session_id: 会话ID
            city: 城市
            latitude: 纬度
            longitude: 经度
            chart_id: 主要星盘ID
            
        Returns:
            OnlineUserPresence 实例
        """
        existing = db.query(OnlineUserPresence).filter(
            OnlineUserPresence.user_id == user_id
        ).first()
        
        now = datetime.utcnow()
        
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
            return existing
        
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
        db.refresh(presence)
        
        return presence
    
    def mark_user_offline(self, db: Session, user_id: int) -> bool:
        """标记用户为离线"""
        presence = db.query(OnlineUserPresence).filter(
            OnlineUserPresence.user_id == user_id
        ).first()
        
        if presence:
            presence.is_online = False
            presence.updated_at = datetime.utcnow()
            db.commit()
            return True
        
        return False
    
    def cleanup_offline_users(self, db: Session) -> int:
        """清理超时的在线用户"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=self._online_timeout_minutes)
        
        count = db.query(OnlineUserPresence).filter(
            and_(
                OnlineUserPresence.is_online == True,
                OnlineUserPresence.last_seen_at < cutoff_time
            )
        ).update(
            {OnlineUserPresence.is_online: False},
            synchronize_session=False
        )
        
        db.commit()
        return count
    
    def get_online_users(
        self,
        db: Session,
        scope: str = "global",
        city: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        radius_km: float = 50.0
    ) -> List[Dict[str, Any]]:
        """
        获取在线用户列表
        
        Args:
            db: 数据库会话
            scope: 范围 ('global' 或 'local')
            city: 城市名称
            latitude: 中心点纬度
            longitude: 中心点经度
            radius_km: 搜索半径（公里）
            
        Returns:
            在线用户列表
        """
        query = db.query(OnlineUserPresence).filter(
            OnlineUserPresence.is_online == True
        )
        
        if scope == "local" and city:
            query = query.filter(OnlineUserPresence.last_city == city)
        
        online_presences = query.all()
        
        result = []
        for presence in online_presences:
            user = db.query(User).filter(User.id == presence.user_id).first()
            chart = None
            
            if presence.primary_chart_id:
                chart = db.query(Chart).filter(Chart.id == presence.primary_chart_id).first()
            
            result.append({
                "user_id": presence.user_id,
                "username": user.username if user else None,
                "city": presence.last_city,
                "latitude": presence.last_latitude,
                "longitude": presence.last_longitude,
                "chart_id": presence.primary_chart_id,
                "chart_data": json.loads(chart.chart_data) if chart and chart.chart_data else None,
                "last_seen_at": presence.last_seen_at.isoformat() if presence.last_seen_at else None
            })
        
        return result
    
    def get_online_user_count(
        self,
        db: Session,
        scope: str = "global",
        city: Optional[str] = None
    ) -> int:
        """获取在线用户数量"""
        query = db.query(func.count(OnlineUserPresence.id)).filter(
            OnlineUserPresence.is_online == True
        )
        
        if scope == "local" and city:
            query = query.filter(OnlineUserPresence.last_city == city)
        
        return query.scalar() or 0
    
    def _calculate_angular_distance(self, lon1: float, lon2: float) -> float:
        """计算两个经度之间的角距离（0-180度）"""
        diff = abs(lon1 - lon2)
        if diff > 180.0:
            diff = 360.0 - diff
        return diff
    
    def _find_aspect_type(self, diff: float) -> Optional[Dict[str, Any]]:
        """查找相位类型"""
        for aspect_type in GROUP_ASPECT_TYPES:
            angle = aspect_type["angle"]
            orb = aspect_type["orb"]
            
            if abs(diff - angle) <= orb:
                orb_used = abs(diff - angle)
                return {
                    "aspect": aspect_type["name"],
                    "aspect_symbol": aspect_type["symbol"],
                    "angle": angle,
                    "actual_angle": round(diff, 4),
                    "orb": round(orb_used, 4),
                    "nature": aspect_type["nature"],
                    "orb_ratio": round((orb - orb_used) / orb, 3)
                }
        return None
    
    def _get_zodiac_sign(self, longitude: float) -> str:
        """根据黄经获取星座"""
        sign_index = int(longitude / 30)
        return ZODIAC_SIGNS[sign_index % 12]
    
    def _get_zodiac_sign_index(self, longitude: float) -> int:
        """根据黄经获取星座索引"""
        return int(longitude / 30) % 12
    
    def aggregate_planet_distribution(
        self,
        db: Session,
        online_users: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        聚合行星分布统计
        
        Args:
            db: 数据库会话
            online_users: 在线用户列表
            
        Returns:
            行星分布统计
        """
        planet_distribution = {
            planet: {sign: 0 for sign in ZODIAC_SIGNS}
            for planet in MAIN_PLANETS
        }
        
        planet_sign_counts = {planet: {} for planet in MAIN_PLANETS}
        total_users_with_chart = 0
        
        for user_data in online_users:
            chart_data = user_data.get("chart_data")
            if not chart_data:
                continue
            
            planets = chart_data.get("planets", [])
            if not planets:
                continue
            
            total_users_with_chart += 1
            
            for planet in planets:
                planet_name = planet.get("name")
                if planet_name not in MAIN_PLANETS:
                    continue
                
                longitude = planet.get("longitude", 0.0)
                sign = self._get_zodiac_sign(longitude)
                
                planet_distribution[planet_name][sign] = planet_distribution[planet_name].get(sign, 0) + 1
                
                if sign not in planet_sign_counts[planet_name]:
                    planet_sign_counts[planet_name][sign] = 0
                planet_sign_counts[planet_name][sign] += 1
        
        dominant_planets = []
        for planet_name, sign_counts in planet_sign_counts.items():
            if not sign_counts:
                continue
            
            max_count = max(sign_counts.values())
            dominant_signs = [sign for sign, count in sign_counts.items() if count == max_count]
            
            for sign in dominant_signs:
                percentage = (max_count / total_users_with_chart * 100) if total_users_with_chart > 0 else 0
                dominant_planets.append({
                    "planet": planet_name,
                    "dominant_sign": sign,
                    "count": max_count,
                    "percentage": round(percentage, 1)
                })
        
        dominant_planets.sort(key=lambda x: x["percentage"], reverse=True)
        
        return {
            "distribution": planet_distribution,
            "dominant_planets": dominant_planets[:5],
            "total_users": total_users_with_chart
        }
    
    def aggregate_aspect_distribution(
        self,
        db: Session,
        online_users: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        聚合相位分布统计
        
        注意：这是计算每个用户本命盘内的相位分布，
        不是用户之间的合盘相位。
        """
        aspect_distribution = {
            "合相": 0,
            "六分相": 0,
            "四分相": 0,
            "三分相": 0,
            "对分相": 0
        }
        
        aspect_by_nature = {
            "harmonious": 0,
            "challenging": 0,
            "neutral": 0
        }
        
        dominant_aspects = []
        total_aspects = 0
        total_users_with_aspects = 0
        
        for user_data in online_users:
            chart_data = user_data.get("chart_data")
            if not chart_data:
                continue
            
            planets = chart_data.get("planets", [])
            if not planets or len(planets) < 2:
                continue
            
            filtered_planets = [p for p in planets if p.get("name") in MAIN_PLANETS]
            if len(filtered_planets) < 2:
                continue
            
            user_aspect_count = 0
            
            for i, p1 in enumerate(filtered_planets):
                for p2 in filtered_planets[i + 1:]:
                    lon1 = p1.get("longitude", 0.0)
                    lon2 = p2.get("longitude", 0.0)
                    
                    diff = self._calculate_angular_distance(lon1, lon2)
                    aspect = self._find_aspect_type(diff)
                    
                    if aspect:
                        aspect_name = aspect["aspect"]
                        nature = aspect["nature"]
                        
                        aspect_distribution[aspect_name] = aspect_distribution.get(aspect_name, 0) + 1
                        aspect_by_nature[nature] = aspect_by_nature.get(nature, 0) + 1
                        total_aspects += 1
                        user_aspect_count += 1
                        
                        dominant_aspects.append({
                            "aspect": aspect_name,
                            "aspect_symbol": aspect["aspect_symbol"],
                            "nature": nature,
                            "planet1": p1.get("name"),
                            "planet2": p2.get("name"),
                            "orb": aspect["orb"]
                        })
            
            if user_aspect_count > 0:
                total_users_with_aspects += 1
        
        dominant_aspect_summary = {}
        for aspect in dominant_aspects:
            key = f"{aspect['planet1']}_{aspect['aspect']}_{aspect['planet2']}"
            if key not in dominant_aspect_summary:
                dominant_aspect_summary[key] = {
                    "aspect": aspect["aspect"],
                    "aspect_symbol": aspect["aspect_symbol"],
                    "planet1": aspect["planet1"],
                    "planet2": aspect["planet2"],
                    "nature": aspect["nature"],
                    "count": 0
                }
            dominant_aspect_summary[key]["count"] += 1
        
        top_dominant_aspects = sorted(
            dominant_aspect_summary.values(),
            key=lambda x: x["count"],
            reverse=True
        )[:10]
        
        return {
            "distribution": aspect_distribution,
            "by_nature": aspect_by_nature,
            "dominant_aspects": top_dominant_aspects,
            "total_aspects": total_aspects,
            "total_users": total_users_with_aspects
        }
    
    def calculate_community_energy(
        self,
        db: Session,
        online_users: List[Dict[str, Any]],
        aspect_distribution: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        计算社区整体能量
        
        Args:
            db: 数据库会话
            online_users: 在线用户列表
            aspect_distribution: 相位分布
            
        Returns:
            社区能量数据
        """
        by_nature = aspect_distribution.get("by_nature", {})
        harmonious = by_nature.get("harmonious", 0)
        challenging = by_nature.get("challenging", 0)
        neutral = by_nature.get("neutral", 0)
        total = harmonious + challenging + neutral
        
        if total == 0:
            base_score = 50.0
            mood = "neutral"
        else:
            harmony_ratio = harmonious / total
            challenge_ratio = challenging / total
            
            base_score = 50 + (harmony_ratio * 30) - (challenge_ratio * 25)
            base_score = max(0, min(100, base_score))
            
            if harmony_ratio > challenge_ratio * 1.5:
                mood = "harmonious"
            elif challenge_ratio > harmony_ratio * 1.5:
                mood = "challenging"
            else:
                mood = "balanced"
        
        dimensions = []
        for dimension in Dimension:
            dim_config = DIMENSION_CONFIG[dimension]
            
            relevant_planets = dim_config.get("planets", [])
            dim_score = base_score * 0.7
            
            random_factor = (hash(f"{dimension.value}_{datetime.utcnow().isoformat()}") % 30 - 15) / 100
            dim_score = base_score * (0.9 + random_factor)
            dim_score = max(0, min(100, dim_score))
            
            if dim_score >= 80:
                level = "high"
                level_label = "旺盛"
            elif dim_score >= 60:
                level = "medium_high"
                level_label = "活跃"
            elif dim_score >= 40:
                level = "medium"
                level_label = "平稳"
            elif dim_score >= 20:
                level = "medium_low"
                level_label = "低迷"
            else:
                level = "low"
                level_label = "停滞"
            
            dimensions.append({
                "dimension": dimension.value,
                "name": dim_config["name"],
                "name_cn": dim_config["name_cn"],
                "icon": dim_config["icon"],
                "color": dim_config["color"],
                "score": round(dim_score, 1),
                "level": level,
                "level_label": level_label
            })
        
        if mood == "harmonious":
            overall_mood_label = "和谐"
            weather_icon = "☀️"
            weather_label = "晴朗"
        elif mood == "challenging":
            overall_mood_label = "紧张"
            weather_icon = "⛈️"
            weather_label = "雷雨"
        else:
            overall_mood_label = "平稳"
            weather_icon = "⛅"
            weather_label = "多云"
        
        return {
            "overall_score": round(base_score, 1),
            "overall_mood": mood,
            "overall_mood_label": overall_mood_label,
            "weather_icon": weather_icon,
            "weather_label": weather_label,
            "dimensions": dimensions,
            "harmonious_count": harmonious,
            "challenging_count": challenging,
            "neutral_count": neutral
        }
    
    def create_snapshot(
        self,
        db: Session,
        scope: str = "global",
        city: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        radius_km: float = 50.0
    ) -> CommunityEnergySnapshot:
        """
        创建社区能量快照
        
        Args:
            db: 数据库会话
            scope: 范围
            city: 城市
            latitude: 纬度
            longitude: 经度
            radius_km: 半径
            
        Returns:
            CommunityEnergySnapshot 实例
        """
        online_users = self.get_online_users(
            db, scope, city, latitude, longitude, radius_km
        )
        
        online_count = len(online_users)
        total_users = db.query(func.count(User.id)).scalar() or 0
        
        planet_distribution = self.aggregate_planet_distribution(db, online_users)
        aspect_distribution = self.aggregate_aspect_distribution(db, online_users)
        community_energy = self.calculate_community_energy(db, online_users, aspect_distribution)
        
        now = datetime.utcnow()
        
        snapshot = CommunityEnergySnapshot(
            snapshot_type="realtime",
            scope=scope,
            scope_city=city,
            scope_latitude=latitude,
            scope_longitude=longitude,
            scope_radius_km=radius_km,
            total_users=total_users,
            online_users=online_count,
            planet_distribution=json.dumps(planet_distribution, ensure_ascii=False),
            aspect_distribution=json.dumps(aspect_distribution, ensure_ascii=False),
            overall_energy_score=community_energy["overall_score"],
            overall_mood=community_energy["overall_mood"],
            dimension_energies=json.dumps(community_energy["dimensions"], ensure_ascii=False),
            dominant_planets=json.dumps(planet_distribution.get("dominant_planets", []), ensure_ascii=False),
            dominant_aspects=json.dumps(aspect_distribution.get("dominant_aspects", []), ensure_ascii=False),
            snapshot_at=now,
            created_at=now
        )
        
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        
        return snapshot
    
    def get_latest_snapshot(
        self,
        db: Session,
        scope: str = "global",
        city: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """获取最新的能量快照"""
        query = db.query(CommunityEnergySnapshot).filter(
            CommunityEnergySnapshot.scope == scope
        )
        
        if scope == "local" and city:
            query = query.filter(CommunityEnergySnapshot.scope_city == city)
        
        query = query.order_by(CommunityEnergySnapshot.snapshot_at.desc())
        snapshot = query.first()
        
        if not snapshot:
            return None
        
        return self._snapshot_to_dict(snapshot)
    
    def get_snapshot_history(
        self,
        db: Session,
        scope: str = "global",
        city: Optional[str] = None,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """获取能量快照历史"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        query = db.query(CommunityEnergySnapshot).filter(
            and_(
                CommunityEnergySnapshot.scope == scope,
                CommunityEnergySnapshot.snapshot_at >= cutoff_time
            )
        )
        
        if scope == "local" and city:
            query = query.filter(CommunityEnergySnapshot.scope_city == city)
        
        query = query.order_by(CommunityEnergySnapshot.snapshot_at)
        snapshots = query.all()
        
        return [self._snapshot_to_dict(s) for s in snapshots]
    
    def _snapshot_to_dict(self, snapshot: CommunityEnergySnapshot) -> Dict[str, Any]:
        """将快照转换为字典"""
        return {
            "id": snapshot.id,
            "snapshot_type": snapshot.snapshot_type,
            "scope": snapshot.scope,
            "scope_city": snapshot.scope_city,
            "total_users": snapshot.total_users,
            "online_users": snapshot.online_users,
            "planet_distribution": json.loads(snapshot.planet_distribution) if snapshot.planet_distribution else None,
            "aspect_distribution": json.loads(snapshot.aspect_distribution) if snapshot.aspect_distribution else None,
            "overall_energy_score": snapshot.overall_energy_score,
            "overall_mood": snapshot.overall_mood,
            "dimension_energies": json.loads(snapshot.dimension_energies) if snapshot.dimension_energies else None,
            "dominant_planets": json.loads(snapshot.dominant_planets) if snapshot.dominant_planets else None,
            "dominant_aspects": json.loads(snapshot.dominant_aspects) if snapshot.dominant_aspects else None,
            "moon_phase": snapshot.moon_phase,
            "mercury_status": snapshot.mercury_status,
            "snapshot_at": snapshot.snapshot_at.isoformat() if snapshot.snapshot_at else None,
            "created_at": snapshot.created_at.isoformat() if snapshot.created_at else None
        }


community_energy_service = CommunityEnergyService()


def get_community_energy_service() -> CommunityEnergyService:
    """获取社区能量服务单例"""
    return community_energy_service
