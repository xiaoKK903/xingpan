import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models import (
    CommunityEnergySnapshot,
    EnergyMission,
    EnergyContribution
)
from app.services.community_energy_service import (
    CommunityEnergyService,
    community_energy_service
)
from app.services.energy_scoring import (
    EnergyScoringEngine,
    Dimension,
    DIMENSION_CONFIG,
    energy_scoring_engine
)

logger = logging.getLogger(__name__)

WEATHER_TYPES = {
    "sunny": {"icon": "☀️", "label": "晴朗", "description": "能量充沛，适合积极行动"},
    "cloudy": {"icon": "⛅", "label": "多云", "description": "能量适中，保持稳健即可"},
    "partly_cloudy": {"icon": "🌤️", "label": "晴间多云", "description": "能量有起伏，需灵活应对"},
    "overcast": {"icon": "🌥️", "label": "阴天", "description": "能量较低，建议调整节奏"},
    "rainy": {"icon": "🌧️", "label": "雷雨", "description": "能量动荡，建议谨慎行事"},
    "stormy": {"icon": "⛈️", "label": "风暴", "description": "能量剧烈波动，需特别注意"}
}

MOOD_LEVELS = {
    "harmonious": {"icon": "😊", "label": "和谐", "color": "#22c55e"},
    "balanced": {"icon": "😐", "label": "平稳", "color": "#64748b"},
    "challenging": {"icon": "😰", "label": "紧张", "color": "#ef4444"}
}

ENERGY_CONTRIBUTION_TYPES = {
    "jupiter": {
        "name": "木星好运",
        "planet": "木星",
        "icon": "♃",
        "color": "#22c55e",
        "description": "注入乐观、扩张、好运能量",
        "base_energy": 10.0,
        "cost_stardust": 5,
        "duration_minutes": 30,
        "target_dimensions": ["wealth", "career", "social"]
    },
    "venus": {
        "name": "金星魅力",
        "planet": "金星",
        "icon": "♀",
        "color": "#ec4899",
        "description": "注入爱、美、社交魅力能量",
        "base_energy": 10.0,
        "cost_stardust": 5,
        "duration_minutes": 30,
        "target_dimensions": ["social", "emotion", "communication"]
    },
    "mars": {
        "name": "火星行动力",
        "planet": "火星",
        "icon": "♂",
        "color": "#ef4444",
        "description": "注入行动、勇气、竞争能量",
        "base_energy": 10.0,
        "cost_stardust": 5,
        "duration_minutes": 30,
        "target_dimensions": ["career", "communication"]
    },
    "mercury": {
        "name": "水星智慧",
        "planet": "水星",
        "icon": "☿",
        "color": "#60a5fa",
        "description": "注入思维、沟通、学习能量",
        "base_energy": 10.0,
        "cost_stardust": 5,
        "duration_minutes": 30,
        "target_dimensions": ["communication", "career"]
    },
    "moon": {
        "name": "月亮情绪",
        "planet": "月亮",
        "icon": "☽",
        "color": "#a78bfa",
        "description": "注入情感、直觉、滋养能量",
        "base_energy": 10.0,
        "cost_stardust": 5,
        "duration_minutes": 30,
        "target_dimensions": ["emotion", "social"]
    },
    "sun": {
        "name": "太阳活力",
        "planet": "太阳",
        "icon": "☉",
        "color": "#f59e0b",
        "description": "注入自信、创造、领导力能量",
        "base_energy": 15.0,
        "cost_stardust": 10,
        "duration_minutes": 45,
        "target_dimensions": ["career", "social", "emotion"]
    }
}


class EnergyWeatherService:
    """
    能量天气播报服务
    
    职责：
    - 生成每日集体情绪指数
    - 生成能量天气播报
    - 分析能量趋势
    - 触发能量任务
    """
    
    def __init__(self):
        self._community_service = community_energy_service
    
    def get_current_weather(
        self,
        db: Session,
        scope: str = "global",
        city: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取当前能量天气
        
        Args:
            db: 数据库会话
            scope: 范围
            city: 城市
            
        Returns:
            能量天气数据
        """
        latest_snapshot = self._community_service.get_latest_snapshot(db, scope, city)
        
        if not latest_snapshot:
            snapshot = self._community_service.create_snapshot(db, scope, city)
            latest_snapshot = self._community_service._snapshot_to_dict(snapshot)
        
        online_users = self._community_service.get_online_users(db, scope, city)
        online_count = len(online_users)
        
        active_contributions = self._get_active_contributions(db, scope, city)
        
        overall_score = latest_snapshot.get("overall_energy_score", 50.0)
        overall_mood = latest_snapshot.get("overall_mood", "balanced")
        
        weather_type = self._score_to_weather(overall_score)
        weather_info = WEATHER_TYPES.get(weather_type, WEATHER_TYPES["cloudy"])
        
        mood_info = MOOD_LEVELS.get(overall_mood, MOOD_LEVELS["balanced"])
        
        dimension_energies = latest_snapshot.get("dimension_energies", [])
        
        high_dimensions = [d for d in dimension_energies if d.get("level") in ["high", "medium_high"]]
        low_dimensions = [d for d in dimension_energies if d.get("level") in ["low", "medium_low"]]
        
        dominant_planets = latest_snapshot.get("dominant_planets", [])
        dominant_aspects = latest_snapshot.get("dominant_aspects", [])
        
        aspect_distribution = latest_snapshot.get("aspect_distribution", {})
        by_nature = aspect_distribution.get("by_nature", {})
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "scope": scope,
            "city": city,
            
            "weather": {
                "type": weather_type,
                "icon": weather_info["icon"],
                "label": weather_info["label"],
                "description": weather_info["description"]
            },
            
            "mood": {
                "type": overall_mood,
                "icon": mood_info["icon"],
                "label": mood_info["label"],
                "color": mood_info["color"]
            },
            
            "energy_score": {
                "current": round(overall_score, 1),
                "min": 0,
                "max": 100
            },
            
            "community_stats": {
                "online_users": online_count,
                "total_users": latest_snapshot.get("total_users", 0),
                "active_contributions": len(active_contributions)
            },
            
            "dimensions": dimension_energies,
            "high_dimensions": high_dimensions,
            "low_dimensions": low_dimensions,
            
            "dominant_planets": dominant_planets[:5],
            "dominant_aspects": dominant_aspects[:5],
            
            "aspect_stats": {
                "harmonious": by_nature.get("harmonious", 0),
                "challenging": by_nature.get("challenging", 0),
                "neutral": by_nature.get("neutral", 0),
                "total": by_nature.get("harmonious", 0) + by_nature.get("challenging", 0) + by_nature.get("neutral", 0)
            },
            
            "active_contributions": active_contributions,
            
            "broadcast": self._generate_broadcast(
                weather_info, mood_info, overall_score, 
                high_dimensions, low_dimensions, dominant_planets
            )
        }
    
    def get_weather_history(
        self,
        db: Session,
        scope: str = "global",
        city: Optional[str] = None,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        获取能量天气历史
        
        Args:
            db: 数据库会话
            scope: 范围
            city: 城市
            hours: 小时数
            
        Returns:
            天气历史数据
        """
        snapshots = self._community_service.get_snapshot_history(db, scope, city, hours)
        
        if not snapshots:
            return {
                "hours": hours,
                "total_points": 0,
                "timestamps": [],
                "scores": [],
                "weathers": [],
                "trend": "stable"
            }
        
        timestamps = []
        scores = []
        weathers = []
        mood_changes = []
        
        for snapshot in snapshots:
            timestamps.append(snapshot.get("snapshot_at"))
            score = snapshot.get("overall_energy_score", 50.0)
            scores.append(score)
            weather_type = self._score_to_weather(score)
            weathers.append(weather_type)
            mood_changes.append(snapshot.get("overall_mood", "balanced"))
        
        if len(scores) >= 2:
            first_score = scores[0]
            last_score = scores[-1]
            
            if last_score > first_score + 10:
                trend = "rising"
            elif last_score < first_score - 10:
                trend = "falling"
            else:
                trend = "stable"
        else:
            trend = "stable"
        
        max_score = max(scores) if scores else 50
        min_score = min(scores) if scores else 50
        avg_score = sum(scores) / len(scores) if scores else 50
        
        return {
            "hours": hours,
            "total_points": len(snapshots),
            "trend": trend,
            
            "timestamps": timestamps,
            "scores": [round(s, 1) for s in scores],
            "weathers": weathers,
            "moods": mood_changes,
            
            "summary": {
                "max_score": round(max_score, 1),
                "min_score": round(min_score, 1),
                "avg_score": round(avg_score, 1),
                "trend": trend
            }
        }
    
    def get_forecast(
        self,
        db: Session,
        scope: str = "global",
        city: Optional[str] = None,
        hours: int = 6
    ) -> Dict[str, Any]:
        """
        获取能量天气预测
        
        Args:
            db: 数据库会话
            scope: 范围
            city: 城市
            hours: 预测小时数
            
        Returns:
            预测数据
        """
        history = self.get_weather_history(db, scope, city, hours=24)
        current = self.get_current_weather(db, scope, city)
        
        scores = history.get("scores", [50.0])
        base_score = scores[-1] if scores else 50.0
        
        forecast_points = []
        now = datetime.utcnow()
        
        for i in range(hours):
            forecast_time = now + timedelta(hours=i + 1)
            
            random_factor = (hash(f"{scope}_{city}_{forecast_time.isoformat()}") % 20 - 10) / 100
            forecast_score = base_score * (1 + random_factor)
            forecast_score = max(0, min(100, forecast_score))
            
            weather_type = self._score_to_weather(forecast_score)
            weather_info = WEATHER_TYPES.get(weather_type, WEATHER_TYPES["cloudy"])
            
            forecast_points.append({
                "time": forecast_time.isoformat(),
                "hour": forecast_time.hour,
                "score": round(forecast_score, 1),
                "weather": weather_type,
                "icon": weather_info["icon"],
                "label": weather_info["label"]
            })
        
        return {
            "forecast_hours": hours,
            "current_score": current.get("energy_score", {}).get("current", 50.0),
            "forecast": forecast_points,
            "note": "此预测基于历史趋势和星象因素，仅供参考"
        }
    
    def check_mission_triggers(
        self,
        db: Session,
        weather_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        检查是否需要触发能量任务
        
        Args:
            db: 数据库会话
            weather_data: 天气数据
            
        Returns:
            触发的任务列表
        """
        triggered = []
        
        energy_score = weather_data.get("energy_score", {}).get("current", 50.0)
        mood_type = weather_data.get("mood", {}).get("type", "balanced")
        low_dimensions = weather_data.get("low_dimensions", [])
        aspect_stats = weather_data.get("aspect_stats", {})
        
        challenging_count = aspect_stats.get("challenging", 0)
        total_aspects = aspect_stats.get("total", 1)
        challenging_ratio = challenging_count / total_aspects if total_aspects > 0 else 0
        
        if challenging_ratio > 0.4 or energy_score < 40:
            mission = self._create_meditation_mission(db, weather_data)
            if mission:
                triggered.append(mission)
        
        if mood_type == "challenging" or energy_score < 30:
            mission = self._create_group_meditation_mission(db, weather_data)
            if mission:
                triggered.append(mission)
        
        for dim in low_dimensions:
            dim_type = dim.get("dimension")
            if dim_type == "emotion" and dim.get("score", 50) < 30:
                mission = self._create_emotion_support_mission(db, weather_data)
                if mission:
                    triggered.append(mission)
            elif dim_type == "social" and dim.get("score", 50) < 30:
                mission = self._create_social_connect_mission(db, weather_data)
                if mission:
                    triggered.append(mission)
        
        return triggered
    
    def _create_meditation_mission(
        self,
        db: Session,
        weather_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """创建冥想任务"""
        now = datetime.utcnow()
        
        existing = db.query(EnergyMission).filter(
            and_(
                EnergyMission.mission_type == "silent_meditation",
                EnergyMission.status == "active",
                EnergyMission.start_at >= now - timedelta(hours=1)
            )
        ).first()
        
        if existing:
            return None
        
        mission = EnergyMission(
            mission_type="silent_meditation",
            title="静音冥想打卡",
            description="当前社区能量较为紧张，让我们一起通过冥想来平复情绪。安静地坐下来，专注于呼吸，感受内心的平静。",
            trigger_condition="challenging_aspects_high",
            target_dimension="emotion",
            difficulty="easy",
            base_reward=10,
            max_participants=100,
            start_at=now,
            end_at=now + timedelta(minutes=30),
            duration_minutes=30,
            status="active",
            participant_count=0,
            energy_contributed=0.0,
            created_at=now,
            updated_at=now
        )
        
        db.add(mission)
        db.commit()
        db.refresh(mission)
        
        return {
            "id": mission.id,
            "type": mission.mission_type,
            "title": mission.title,
            "description": mission.description,
            "start_at": mission.start_at.isoformat() if mission.start_at else None,
            "end_at": mission.end_at.isoformat() if mission.end_at else None,
            "reward": mission.base_reward
        }
    
    def _create_group_meditation_mission(
        self,
        db: Session,
        weather_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """创建集体共修任务"""
        now = datetime.utcnow()
        
        existing = db.query(EnergyMission).filter(
            and_(
                EnergyMission.mission_type == "group_meditation",
                EnergyMission.status == "active",
                EnergyMission.start_at >= now - timedelta(hours=2)
            )
        ).first()
        
        if existing:
            return None
        
        mission = EnergyMission(
            mission_type="group_meditation",
            title="集体共修",
            description="社区能量处于低谷，让我们一起进行集体共修。想象金色的光芒从宇宙注入社区，每个人都分享爱与和平的能量。",
            trigger_condition="low_energy_community",
            target_dimension="emotion",
            difficulty="medium",
            base_reward=25,
            max_participants=200,
            start_at=now,
            end_at=now + timedelta(minutes=45),
            duration_minutes=45,
            status="active",
            participant_count=0,
            energy_contributed=0.0,
            created_at=now,
            updated_at=now
        )
        
        db.add(mission)
        db.commit()
        db.refresh(mission)
        
        return {
            "id": mission.id,
            "type": mission.mission_type,
            "title": mission.title,
            "description": mission.description,
            "start_at": mission.start_at.isoformat() if mission.start_at else None,
            "end_at": mission.end_at.isoformat() if mission.end_at else None,
            "reward": mission.base_reward
        }
    
    def _create_emotion_support_mission(
        self,
        db: Session,
        weather_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """创建情绪支持任务"""
        now = datetime.utcnow()
        
        existing = db.query(EnergyMission).filter(
            and_(
                EnergyMission.mission_type == "emotion_support",
                EnergyMission.status == "active",
                EnergyMission.start_at >= now - timedelta(hours=3)
            )
        ).first()
        
        if existing:
            return None
        
        mission = EnergyMission(
            mission_type="emotion_support",
            title="情绪能量共振",
            description="社区情绪维度能量较低，让我们一起进行情绪能量共振。回想一次让你感到温暖的经历，将这份温暖发送给社区中的每个人。",
            trigger_condition="low_emotion_energy",
            target_dimension="emotion",
            difficulty="medium",
            base_reward=20,
            max_participants=150,
            start_at=now,
            end_at=now + timedelta(minutes=40),
            duration_minutes=40,
            status="active",
            participant_count=0,
            energy_contributed=0.0,
            created_at=now,
            updated_at=now
        )
        
        db.add(mission)
        db.commit()
        db.refresh(mission)
        
        return {
            "id": mission.id,
            "type": mission.mission_type,
            "title": mission.title,
            "description": mission.description,
            "start_at": mission.start_at.isoformat() if mission.start_at else None,
            "end_at": mission.end_at.isoformat() if mission.end_at else None,
            "reward": mission.base_reward
        }
    
    def _create_social_connect_mission(
        self,
        db: Session,
        weather_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """创建社交连接任务"""
        now = datetime.utcnow()
        
        existing = db.query(EnergyMission).filter(
            and_(
                EnergyMission.mission_type == "social_connect",
                EnergyMission.status == "active",
                EnergyMission.start_at >= now - timedelta(hours=3)
            )
        ).first()
        
        if existing:
            return None
        
        mission = EnergyMission(
            mission_type="social_connect",
            title="微笑连接任务",
            description="社区社交维度能量较低，让我们一起进行微笑连接。在心中向社区中的每个人发送一个温暖的微笑，想象彼此之间建立起金色的连接。",
            trigger_condition="low_social_energy",
            target_dimension="social",
            difficulty="easy",
            base_reward=15,
            max_participants=200,
            start_at=now,
            end_at=now + timedelta(minutes=30),
            duration_minutes=30,
            status="active",
            participant_count=0,
            energy_contributed=0.0,
            created_at=now,
            updated_at=now
        )
        
        db.add(mission)
        db.commit()
        db.refresh(mission)
        
        return {
            "id": mission.id,
            "type": mission.mission_type,
            "title": mission.title,
            "description": mission.description,
            "start_at": mission.start_at.isoformat() if mission.start_at else None,
            "end_at": mission.end_at.isoformat() if mission.end_at else None,
            "reward": mission.base_reward
        }
    
    def _get_active_contributions(
        self,
        db: Session,
        scope: str,
        city: Optional[str]
    ) -> List[Dict[str, Any]]:
        """获取活跃的能量贡献"""
        now = datetime.utcnow()
        
        query = db.query(EnergyContribution).filter(
            and_(
                EnergyContribution.is_active == True,
                EnergyContribution.expires_at > now
            )
        )
        
        if scope == "local" and city:
            pass
        
        contributions = query.order_by(EnergyContribution.created_at.desc()).all()
        
        result = []
        for contrib in contributions:
            contrib_type = ENERGY_CONTRIBUTION_TYPES.get(contrib.contribution_type, {})
            
            result.append({
                "id": contrib.id,
                "type": contrib.contribution_type,
                "planet": contrib.planet_name,
                "planet_icon": contrib_type.get("icon", "✨"),
                "name": contrib_type.get("name", "未知贡献"),
                "description": contrib_type.get("description", ""),
                "color": contrib_type.get("color", "#9370db"),
                "energy_amount": contrib.energy_amount,
                "target_dimension": contrib.target_dimension,
                "created_at": contrib.created_at.isoformat() if contrib.created_at else None,
                "expires_at": contrib.expires_at.isoformat() if contrib.expires_at else None
            })
        
        return result
    
    def _score_to_weather(self, score: float) -> str:
        """将分数转换为天气类型"""
        if score >= 80:
            return "sunny"
        elif score >= 65:
            return "cloudy"
        elif score >= 50:
            return "partly_cloudy"
        elif score >= 30:
            return "overcast"
        elif score >= 15:
            return "rainy"
        else:
            return "stormy"
    
    def _generate_broadcast(
        self,
        weather_info: Dict[str, Any],
        mood_info: Dict[str, Any],
        score: float,
        high_dimensions: List[Dict[str, Any]],
        low_dimensions: List[Dict[str, Any]],
        dominant_planets: List[Dict[str, Any]]
    ) -> str:
        """生成能量天气播报文本"""
        broadcast_parts = []
        
        broadcast_parts.append(f"【今日能量天气】{weather_info['icon']} {weather_info['label']}")
        broadcast_parts.append(f"当前社区能量指数: {round(score, 1)} / 100")
        broadcast_parts.append(f"整体情绪状态: {mood_info['icon']} {mood_info['label']}")
        
        if dominant_planets:
            top_planet = dominant_planets[0]
            broadcast_parts.append(f"🌟 主导行星: {top_planet['planet']} 在 {top_planet['dominant_sign']} ({top_planet['percentage']}%)")
        
        if high_dimensions:
            dim_names = "、".join([d.get("name_cn", "") for d in high_dimensions[:3]])
            broadcast_parts.append(f"✨ 能量旺盛维度: {dim_names}")
        
        if low_dimensions:
            dim_names = "、".join([d.get("name_cn", "") for d in low_dimensions[:3]])
            broadcast_parts.append(f"⚠️ 能量较低维度: {dim_names}")
        
        broadcast_parts.append(f"💡 建议: {weather_info['description']}")
        
        return "\n".join(broadcast_parts)


energy_weather_service = EnergyWeatherService()


def get_energy_weather_service() -> EnergyWeatherService:
    """获取能量天气服务单例"""
    return energy_weather_service
