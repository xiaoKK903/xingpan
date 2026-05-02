import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from math import sin, cos, sqrt, atan2, radians
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models import OnlineUserPresence, CommunityEnergySnapshot, User

logger = logging.getLogger(__name__)

CHINA_BOUNDS = {
    "min_lat": 18.0,
    "max_lat": 54.0,
    "min_lon": 73.0,
    "max_lon": 135.0
}

GRID_SIZE = 1.0
INFLUENCE_RADIUS_KM = 100.0


class CommunityEnergyMapService:
    """
    同城能量云图服务
    
    职责：
    - 基于地理位置的能量聚合
    - 生成同城能量云图数据
    - 支持热力图可视化
    - 计算集体共振强度
    """
    
    def __init__(self):
        self._influence_decay = 0.5
        self._cache_ttl_seconds = 300
    
    def _calculate_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        计算两点之间的距离（公里）
        
        使用 Haversine 公式
        """
        R = 6371.0
        
        lat1_rad = radians(lat1)
        lon1_rad = radians(lon1)
        lat2_rad = radians(lat2)
        lon2_rad = radians(lon2)
        
        dlon = lon2_rad - lon1_rad
        dlat = lat2_rad - lat1_rad
        
        a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        
        return R * c
    
    def _generate_grid_points(self) -> List[Dict[str, float]]:
        """生成中国区域的网格点"""
        points = []
        
        lat = CHINA_BOUNDS["min_lat"]
        while lat <= CHINA_BOUNDS["max_lat"]:
            lon = CHINA_BOUNDS["min_lon"]
            while lon <= CHINA_BOUNDS["max_lon"]:
                points.append({
                    "lat": round(lat, 1),
                    "lon": round(lon, 1)
                })
                lon += GRID_SIZE
            lat += GRID_SIZE
        
        return points
    
    def get_energy_heatmap(
        self,
        db: Session,
        scope: str = "local",
        city: Optional[str] = None,
        center_lat: Optional[float] = None,
        center_lon: Optional[float] = None,
        radius_km: float = 200.0
    ) -> Dict[str, Any]:
        """
        获取能量热力图数据
        
        Args:
            db: 数据库会话
            scope: 范围
            city: 城市名称
            center_lat: 中心点纬度
            center_lon: 中心点经度
            radius_km: 搜索半径（公里）
            
        Returns:
            热力图数据
        """
        query = db.query(OnlineUserPresence).filter(
            and_(
                OnlineUserPresence.is_online == True,
                OnlineUserPresence.last_latitude.isnot(None),
                OnlineUserPresence.last_longitude.isnot(None)
            )
        )
        
        if scope == "local" and city:
            query = query.filter(OnlineUserPresence.last_city == city)
        
        online_users = query.all()
        
        if not online_users:
            return {
                "heatmap_points": [],
                "summary": {
                    "total_users": 0,
                    "grid_points": 0,
                    "max_intensity": 0,
                    "average_intensity": 0
                },
                "bounds": CHINA_BOUNDS,
                "generated_at": datetime.utcnow().isoformat()
            }
        
        user_locations = []
        for user in online_users:
            user_locations.append({
                "user_id": user.user_id,
                "lat": user.last_latitude,
                "lon": user.last_longitude,
                "city": user.last_city
            })
        
        if center_lat and center_lon:
            filtered_locations = []
            for loc in user_locations:
                dist = self._calculate_distance(
                    center_lat, center_lon,
                    loc["lat"], loc["lon"]
                )
                if dist <= radius_km:
                    filtered_locations.append(loc)
            user_locations = filtered_locations
        
        heatmap_points = self._generate_heatmap_points(user_locations)
        
        max_intensity = 0
        total_intensity = 0
        for point in heatmap_points:
            intensity = point["intensity"]
            max_intensity = max(max_intensity, intensity)
            total_intensity += intensity
        
        avg_intensity = total_intensity / len(heatmap_points) if heatmap_points else 0
        
        resonance_score = self._calculate_collective_resonance(user_locations)
        
        return {
            "heatmap_points": heatmap_points,
            "summary": {
                "total_users": len(user_locations),
                "grid_points": len(heatmap_points),
                "max_intensity": round(max_intensity, 2),
                "average_intensity": round(avg_intensity, 2),
                "collective_resonance_score": round(resonance_score, 2)
            },
            "bounds": self._calculate_bounds(user_locations) if user_locations else CHINA_BOUNDS,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def _generate_heatmap_points(
        self,
        user_locations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        生成热力图点数据
        
        每个用户会对周围的网格点产生影响，
        影响强度随距离衰减
        """
        if not user_locations:
            return []
        
        min_lat = min(loc["lat"] for loc in user_locations) - 1.0
        max_lat = max(loc["lat"] for loc in user_locations) + 1.0
        min_lon = min(loc["lon"] for loc in user_locations) - 1.0
        max_lon = max(loc["lon"] for loc in user_locations) + 1.0
        
        grid_points = []
        lat = min_lat
        while lat <= max_lat:
            lon = min_lon
            while lon <= max_lon:
                grid_points.append({
                    "lat": round(lat, 1),
                    "lon": round(lon, 1),
                    "intensity": 0.0
                })
                lon += GRID_SIZE
            lat += GRID_SIZE
        
        for grid_point in grid_points:
            total_intensity = 0.0
            
            for user_loc in user_locations:
                distance = self._calculate_distance(
                    grid_point["lat"], grid_point["lon"],
                    user_loc["lat"], user_loc["lon"]
                )
                
                if distance <= INFLUENCE_RADIUS_KM:
                    decay = 1.0 - (distance / INFLUENCE_RADIUS_KM)
                    decay = decay ** self._influence_decay
                    total_intensity += decay
            
            grid_point["intensity"] = round(total_intensity, 3)
        
        return [p for p in grid_points if p["intensity"] > 0]
    
    def _calculate_collective_resonance(
        self,
        user_locations: List[Dict[str, Any]]
    ) -> float:
        """
        计算集体共振强度
        
        基于用户密度和分布计算共振分数
        """
        if len(user_locations) < 2:
            return 0.0
        
        total_distance = 0.0
        pair_count = 0
        
        for i, loc1 in enumerate(user_locations):
            for loc2 in user_locations[i + 1:]:
                distance = self._calculate_distance(
                    loc1["lat"], loc1["lon"],
                    loc2["lat"], loc2["lon"]
                )
                total_distance += distance
                pair_count += 1
        
        if pair_count == 0:
            return 0.0
        
        avg_distance = total_distance / pair_count
        
        density_factor = len(user_locations) / 100.0
        
        distance_factor = max(0, 1.0 - avg_distance / 500.0)
        
        resonance_score = (density_factor * 0.5 + distance_factor * 0.5) * 100
        resonance_score = min(100, max(0, resonance_score))
        
        return resonance_score
    
    def _calculate_bounds(
        self,
        user_locations: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """计算用户分布的边界"""
        if not user_locations:
            return CHINA_BOUNDS
        
        return {
            "min_lat": min(loc["lat"] for loc in user_locations) - 0.5,
            "max_lat": max(loc["lat"] for loc in user_locations) + 0.5,
            "min_lon": min(loc["lon"] for loc in user_locations) - 0.5,
            "max_lon": max(loc["lon"] for loc in user_locations) + 0.5
        }
    
    def get_city_energy_rankings(
        self,
        db: Session,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        获取城市能量排名
        
        Args:
            db: 数据库会话
            limit: 返回数量
            
        Returns:
            城市能量排名列表
        """
        result = db.query(
            OnlineUserPresence.last_city,
            func.count(OnlineUserPresence.id).label('user_count')
        ).filter(
            and_(
                OnlineUserPresence.is_online == True,
                OnlineUserPresence.last_city.isnot(None)
            )
        ).group_by(
            OnlineUserPresence.last_city
        ).order_by(
            func.count(OnlineUserPresence.id).desc()
        ).limit(limit).all()
        
        rankings = []
        for i, (city, user_count) in enumerate(result):
            energy_score = self._calculate_city_energy_score(user_count)
            
            rankings.append({
                "rank": i + 1,
                "city": city,
                "online_users": user_count,
                "energy_score": round(energy_score, 1),
                "resonance_level": self._get_resonance_level(energy_score)
            })
        
        return rankings
    
    def _calculate_city_energy_score(self, user_count: int) -> float:
        """
        计算城市能量分数
        
        基于在线用户数量的对数缩放
        """
        if user_count == 0:
            return 0.0
        
        import math
        base_score = math.log1p(user_count) * 20
        
        return min(100, base_score)
    
    def _get_resonance_level(self, score: float) -> str:
        """根据分数获取共振等级"""
        if score >= 80:
            return "high"
        elif score >= 60:
            return "medium_high"
        elif score >= 40:
            return "medium"
        elif score >= 20:
            return "medium_low"
        else:
            return "low"
    
    def get_regional_energy_summary(
        self,
        db: Session
    ) -> Dict[str, Any]:
        """
        获取区域能量汇总
        
        Args:
            db: 数据库会话
            
        Returns:
            区域能量汇总
        """
        city_rankings = self.get_city_energy_rankings(db, limit=10)
        
        total_online = db.query(func.count(OnlineUserPresence.id)).filter(
            OnlineUserPresence.is_online == True
        ).scalar() or 0
        
        cities_with_users = db.query(
            func.count(func.distinct(OnlineUserPresence.last_city))
        ).filter(
            and_(
                OnlineUserPresence.is_online == True,
                OnlineUserPresence.last_city.isnot(None)
            )
        ).scalar() or 0
        
        top_city = city_rankings[0] if city_rankings else None
        
        return {
            "summary": {
                "total_online_users": total_online,
                "cities_covered": cities_with_users,
                "top_city": top_city
            },
            "city_rankings": city_rankings,
            "generated_at": datetime.utcnow().isoformat()
        }


community_energy_map_service = CommunityEnergyMapService()


def get_community_energy_map_service() -> CommunityEnergyMapService:
    """获取社区能量云图服务单例"""
    return community_energy_map_service
