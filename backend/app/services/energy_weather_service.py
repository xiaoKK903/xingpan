import logging
import json
import random
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from sqlalchemy.orm import Session

from app.services.ephemeris_calculator import get_ephemeris_calculator
from app.services.transit_service import (
    get_transit_analysis_engine,
    calculate_moon_phase,
    check_mercury_retrograde
)
from app.services.community_energy_service import community_energy_service
from app.astro import MAIN_PLANETS, longitude_to_zodiac

logger = logging.getLogger(__name__)

ephemeris = get_ephemeris_calculator()
transit_engine = get_transit_analysis_engine()


class WeatherSeverity(str, Enum):
    CLEAR = "clear"
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


class CollectiveMood(str, Enum):
    HARMONIOUS = "harmonious"
    BALANCED = "balanced"
    TENSE = "tense"
    CHALLENGING = "challenging"


WEATHER_SEVERITY_CONFIG = {
    WeatherSeverity.CLEAR: {
        "label": "晴朗",
        "icon": "☀️",
        "color": "#F59E0B",
        "bg_color": "#FFFBEB",
        "description": "星象晴朗，能量充沛，适合积极行动。"
    },
    WeatherSeverity.MILD: {
        "label": "多云",
        "icon": "⛅",
        "color": "#6B7280",
        "bg_color": "#F3F4F6",
        "description": "星象多云，能量适中，保持稳健即可。"
    },
    WeatherSeverity.MODERATE: {
        "label": "阴天",
        "icon": "🌥️",
        "color": "#4B5563",
        "bg_color": "#E5E7EB",
        "description": "星象阴沉，能量较低，建议调整节奏。"
    },
    WeatherSeverity.SEVERE: {
        "label": "雷雨",
        "icon": "⛈️",
        "color": "#DC2626",
        "bg_color": "#FEF2F2",
        "description": "星象动荡，建议谨慎行事，避免冲动决策。",
        "is_warning": True
    },
    WeatherSeverity.CRITICAL: {
        "label": "红色预警",
        "icon": "🚨",
        "color": "#991B1B",
        "bg_color": "#FEE2E2",
        "description": "凶星天象强烈，务必谨慎行事，避免重大决策。",
        "is_warning": True,
        "is_critical": True
    }
}


OMINOUS_EVENTS = {
    "mercury_retrograde": {
        "name": "水星逆行",
        "planet": "水星",
        "icon": "☿",
        "severity": WeatherSeverity.SEVERE,
        "description": "水星逆行期间，注意沟通细节、电子设备备份、出行计划预留缓冲时间。",
        "affected_areas": ["沟通", "交通", "电子设备", "合同签署"],
        "recommendations": [
            "备份重要数据",
            "出行预留缓冲时间",
            "沟通时保持耐心",
            "避免签署重要合同"
        ]
    },
    "mars_retrograde": {
        "name": "火星逆行",
        "planet": "火星",
        "icon": "♂",
        "severity": WeatherSeverity.CRITICAL,
        "description": "火星逆行期间，行动力受阻，容易冲动或压抑愤怒，需特别注意安全和情绪管理。",
        "affected_areas": ["行动力", "情绪", "安全", "竞争"],
        "recommendations": [
            "避免冲动决策",
            "注意安全防护",
            "合理释放情绪",
            "推迟重大行动"
        ]
    },
    "saturn_retrograde": {
        "name": "土星逆行",
        "planet": "土星",
        "icon": "♄",
        "severity": WeatherSeverity.SEVERE,
        "description": "土星逆行期间，业力显现，过去的责任和未完成的事业需要面对。",
        "affected_areas": ["责任", "业力", "事业", "限制"],
        "recommendations": [
            "面对过去未完成的责任",
            "重新评估长期目标",
            "保持耐心和坚持",
            "学会放下负担"
        ]
    },
    "mars_square_saturn": {
        "name": "火星四分土星",
        "planets": ["火星", "土星"],
        "icon": "♂□♄",
        "severity": WeatherSeverity.CRITICAL,
        "description": "火星与土星形成四分相，行动欲望与现实限制剧烈冲突，容易产生挫折感和愤怒。",
        "affected_areas": ["行动力", "限制", "挫折", "愤怒"],
        "recommendations": [
            "保持冷静，避免冲动",
            "将挫折转化为动力",
            "接受现实限制",
            "寻找建设性的出口"
        ]
    },
    "uranus_square_pluto": {
        "name": "天王星四分冥王星",
        "planets": ["天王星", "冥王星"],
        "icon": "♅□♇",
        "severity": WeatherSeverity.CRITICAL,
        "description": "天王星与冥王星形成四分相，突变与深层转化的冲突，社会结构和个人生活都可能经历剧变。",
        "affected_areas": ["突变", "转化", "权力", "社会变革"],
        "recommendations": [
            "保持灵活，适应变化",
            "放下控制欲",
            "拥抱不确定性",
            "寻找内心的稳定"
        ]
    },
    "full_moon_eclipse": {
        "name": "月食",
        "planet": "月亮",
        "icon": "🌕",
        "severity": WeatherSeverity.SEVERE,
        "description": "月食期间，情绪能量被放大，可能带来情绪的释放和关系的转折。",
        "affected_areas": ["情绪", "关系", "释放", "完结"],
        "recommendations": [
            "注意情绪波动",
            "适合释放和放下",
            "关注亲密关系",
            "保持情绪平衡"
        ]
    },
    "solar_eclipse": {
        "name": "日食",
        "planet": "太阳",
        "icon": "🌑",
        "severity": WeatherSeverity.SEVERE,
        "description": "日食期间，新的开始被强调，但也可能伴随着不确定性。",
        "affected_areas": ["新开始", "自我", "目标", "不确定性"],
        "recommendations": [
            "设定新意图",
            "保持开放心态",
            "观察而非强迫",
            "为新机会做好准备"
        ]
    }
}


ENERGY_CONTRIBUTION_TYPES = {
    "sun_energy": {
        "name": "太阳能量",
        "planet": "太阳",
        "icon": "☀️",
        "color": "#F59E0B",
        "description": "注入太阳的光芒和活力，提升自信和创造力",
        "base_energy": 15.0,
        "cost_stardust": 8,
        "duration_minutes": 60,
        "target_dimensions": ["career", "social"]
    },
    "moon_energy": {
        "name": "月亮能量",
        "planet": "月亮",
        "icon": "🌙",
        "color": "#8B5CF6",
        "description": "注入月亮的温柔和直觉，提升情绪感知力",
        "base_energy": 12.0,
        "cost_stardust": 6,
        "duration_minutes": 45,
        "target_dimensions": ["emotion", "social"]
    },
    "mercury_energy": {
        "name": "水星能量",
        "planet": "水星",
        "icon": "☿",
        "color": "#10B981",
        "description": "注入水星的智慧和敏捷，提升沟通和思维能力",
        "base_energy": 10.0,
        "cost_stardust": 5,
        "duration_minutes": 30,
        "target_dimensions": ["communication", "career"]
    },
    "venus_energy": {
        "name": "金星能量",
        "planet": "金星",
        "icon": "♀",
        "color": "#EC4899",
        "description": "注入金星的爱与美，提升社交和财运",
        "base_energy": 14.0,
        "cost_stardust": 7,
        "duration_minutes": 50,
        "target_dimensions": ["social", "wealth"]
    },
    "mars_energy": {
        "name": "火星能量",
        "planet": "火星",
        "icon": "♂",
        "color": "#EF4444",
        "description": "注入火星的勇气和行动力，提升竞争和行动力",
        "base_energy": 18.0,
        "cost_stardust": 10,
        "duration_minutes": 60,
        "target_dimensions": ["career", "emotion"]
    },
    "jupiter_energy": {
        "name": "木星能量",
        "planet": "木星",
        "icon": "♃",
        "color": "#3B82F6",
        "description": "注入木星的扩张和幸运，提升各领域运势",
        "base_energy": 20.0,
        "cost_stardust": 12,
        "duration_minutes": 90,
        "target_dimensions": ["wealth", "career", "social"]
    },
    "saturn_energy": {
        "name": "土星能量",
        "planet": "土星",
        "icon": "♄",
        "color": "#6B7280",
        "description": "注入土星的稳定和责任，提升长期规划能力",
        "base_energy": 16.0,
        "cost_stardust": 9,
        "duration_minutes": 75,
        "target_dimensions": ["career", "wealth"]
    }
}


WARM_MISSION_TEMPLATES = {
    "harmonious_high": [
        {
            "id": "compliment_others",
            "title": "善意赞美",
            "description": "在广场上找到一位用户，真心赞美他们的星盘特质或头像",
            "difficulty": "easy",
            "base_reward": 15,
            "duration_minutes": 10,
            "mood_trigger": "harmonious",
            "energy_requirement": 5.0,
            "mission_type": "social_interaction"
        },
        {
            "id": "share_gratitude",
            "title": "感恩分享",
            "description": "分享一件今天让你感恩的事情，传递正能量",
            "difficulty": "easy",
            "base_reward": 12,
            "duration_minutes": 5,
            "mood_trigger": "harmonious",
            "energy_requirement": 3.0,
            "mission_type": "expression"
        },
        {
            "id": "join_encounter",
            "title": "缘分相遇",
            "description": "主动发起一次广场相遇，与他人建立连接",
            "difficulty": "medium",
            "base_reward": 25,
            "duration_minutes": 15,
            "mood_trigger": "harmonious",
            "energy_requirement": 10.0,
            "mission_type": "encounter"
        }
    ],
    "balanced": [
        {
            "id": "check_horoscope",
            "title": "今日运势",
            "description": "查看你的每日运势，了解今日能量指引",
            "difficulty": "easy",
            "base_reward": 8,
            "duration_minutes": 3,
            "mood_trigger": "balanced",
            "energy_requirement": 0.0,
            "mission_type": "exploration"
        },
        {
            "id": "review_chart",
            "title": "星盘回顾",
            "description": "回顾你的本命盘，发现一个你之前忽略的特质",
            "difficulty": "medium",
            "base_reward": 18,
            "duration_minutes": 8,
            "mood_trigger": "balanced",
            "energy_requirement": 5.0,
            "mission_type": "self_reflection"
        },
        {
            "id": "energy_contribution",
            "title": "能量注入",
            "description": "向广场注入一份行星能量，提升集体场域",
            "difficulty": "medium",
            "base_reward": 20,
            "duration_minutes": 5,
            "mood_trigger": "balanced",
            "energy_requirement": 8.0,
            "mission_type": "contribution"
        }
    ],
    "tense": [
        {
            "id": "deep_breath",
            "title": "深呼吸",
            "description": "花一分钟时间深呼吸，让自己平静下来",
            "difficulty": "easy",
            "base_reward": 10,
            "duration_minutes": 2,
            "mood_trigger": "tense",
            "energy_requirement": 0.0,
            "mission_type": "self_care"
        },
        {
            "id": "write_journal",
            "title": "情绪日记",
            "description": "写下此刻的情绪感受，表达而不压抑",
            "difficulty": "easy",
            "base_reward": 12,
            "duration_minutes": 5,
            "mood_trigger": "tense",
            "energy_requirement": 2.0,
            "mission_type": "expression"
        },
        {
            "id": "seek_support",
            "title": "寻求支持",
            "description": "在广场上找到一位让你感到安全的人，分享你的感受",
            "difficulty": "medium",
            "base_reward": 30,
            "duration_minutes": 15,
            "mood_trigger": "tense",
            "energy_requirement": 10.0,
            "mission_type": "social_interaction"
        }
    ],
    "challenging": [
        {
            "id": "grounding_exercise",
            "title": "接地练习",
            "description": "感受你的双脚，与大地连接，让自己稳定下来",
            "difficulty": "easy",
            "base_reward": 15,
            "duration_minutes": 3,
            "mood_trigger": "challenging",
            "energy_requirement": 0.0,
            "mission_type": "self_care"
        },
        {
            "id": "self_compassion",
            "title": "自我慈悲",
            "description": "对自己说几句温柔的话，就像对待最好的朋友一样",
            "difficulty": "easy",
            "base_reward": 15,
            "duration_minutes": 3,
            "mood_trigger": "challenging",
            "energy_requirement": 0.0,
            "mission_type": "self_care"
        },
        {
            "id": "energy_balancing",
            "title": "能量平衡",
            "description": "查看你的元素能量分布，找出需要调整的地方",
            "difficulty": "medium",
            "base_reward": 25,
            "duration_minutes": 10,
            "mood_trigger": "challenging",
            "energy_requirement": 5.0,
            "mission_type": "self_reflection"
        },
        {
            "id": "professional_help",
            "title": "专业支持",
            "description": "如果感到困难，考虑寻求专业心理咨询师的帮助",
            "difficulty": "easy",
            "base_reward": 20,
            "duration_minutes": 1,
            "mood_trigger": "challenging",
            "energy_requirement": 0.0,
            "mission_type": "awareness"
        }
    ]
}


@dataclass
class EnergyWeatherSnapshot:
    snapshot_id: str
    timestamp: datetime
    
    overall_energy_score: float
    collective_mood: str
    collective_mood_label: str
    
    weather_severity: WeatherSeverity
    weather_label: str
    weather_icon: str
    
    online_user_count: int
    users_with_chart: int
    
    dominant_planets: List[Dict[str, Any]]
    dominant_aspects: List[Dict[str, Any]]
    
    ominous_events: List[Dict[str, Any]]
    has_warning: bool
    warning_level: str
    
    dimension_energies: List[Dict[str, Any]]
    
    moon_phase: Optional[Dict[str, Any]] = None
    mercury_status: Optional[Dict[str, Any]] = None
    
    transit_aspects: List[Dict[str, Any]] = field(default_factory=list)
    
    triggered_missions: List[Dict[str, Any]] = field(default_factory=list)


class EnergyWeatherService:
    """
    能量气象站服务
    
    职责：
    - 每小时统计在线用户星盘 + 天象夹角
    - 计算全场当日能量值
    - 检测凶星天象并预警
    - 根据集体情绪推送暖心小任务
    - 管理星元碎片奖励
    """
    
    def __init__(self):
        self._last_snapshot: Optional[EnergyWeatherSnapshot] = None
        self._snapshot_history: List[EnergyWeatherSnapshot] = []
        self._max_history_size = 24
    
    def detect_current_transit_events(self, db: Session) -> List[Dict[str, Any]]:
        """
        检测当前的天象事件，包括凶星天象
        
        Returns:
            事件列表，按严重程度排序
        """
        events = []
        now = datetime.now()
        
        try:
            jd, _ = ephemeris.local_time_to_julday(
                now.year, now.month, now.day,
                now.hour, now.minute,
                39.9042, 116.4074
            )
            
            moon_phase = calculate_moon_phase(jd)
            if moon_phase.get("is_full_moon"):
                events.append({
                    "type": "lunar_event",
                    "event_key": "full_moon",
                    "name": "满月",
                    "icon": "🌕",
                    "severity": WeatherSeverity.MILD.value,
                    "description": "今日满月，情绪能量高涨。",
                    "is_ominous": False
                })
            elif moon_phase.get("is_new_moon"):
                events.append({
                    "type": "lunar_event",
                    "event_key": "new_moon",
                    "name": "新月",
                    "icon": "🌑",
                    "severity": WeatherSeverity.MILD.value,
                    "description": "今日新月，适合设定新目标。",
                    "is_ominous": False
                })
            
            mercury_retro = check_mercury_retrograde(jd)
            if mercury_retro.get("is_retrograde"):
                ominous_config = OMINOUS_EVENTS["mercury_retrograde"]
                events.append({
                    "type": "planetary_event",
                    "event_key": "mercury_retrograde",
                    "name": ominous_config["name"],
                    "planet": ominous_config["planet"],
                    "icon": ominous_config["icon"],
                    "severity": ominous_config["severity"].value,
                    "description": ominous_config["description"],
                    "affected_areas": ominous_config["affected_areas"],
                    "recommendations": ominous_config["recommendations"],
                    "is_ominous": True,
                    "is_warning": True
                })
            
            transit_planets = ephemeris.calculate_multiple_planets(jd, MAIN_PLANETS)
            
            for planet in transit_planets:
                if planet.get("is_retrograde"):
                    planet_name = planet.get("name", "")
                    
                    if planet_name == "火星":
                        ominous_config = OMINOUS_EVENTS["mars_retrograde"]
                        events.append({
                            "type": "planetary_event",
                            "event_key": "mars_retrograde",
                            "name": ominous_config["name"],
                            "planet": ominous_config["planet"],
                            "icon": ominous_config["icon"],
                            "severity": ominous_config["severity"].value,
                            "description": ominous_config["description"],
                            "affected_areas": ominous_config["affected_areas"],
                            "recommendations": ominous_config["recommendations"],
                            "is_ominous": True,
                            "is_warning": True,
                            "is_critical": True
                        })
                    elif planet_name == "土星":
                        ominous_config = OMINOUS_EVENTS["saturn_retrograde"]
                        events.append({
                            "type": "planetary_event",
                            "event_key": "saturn_retrograde",
                            "name": ominous_config["name"],
                            "planet": ominous_config["planet"],
                            "icon": ominous_config["icon"],
                            "severity": ominous_config["severity"].value,
                            "description": ominous_config["description"],
                            "affected_areas": ominous_config["affected_areas"],
                            "recommendations": ominous_config["recommendations"],
                            "is_ominous": True,
                            "is_warning": True
                        })
            
            aspects = ephemeris.calculate_all_aspects(transit_planets, transit_planets)
            
            for aspect in aspects:
                p1 = aspect.get("planet1_name", "")
                p2 = aspect.get("planet2_name", "")
                aspect_type = aspect.get("name", "")
                nature = aspect.get("nature", "neutral")
                
                if ((p1 == "火星" and p2 == "土星") or (p1 == "土星" and p2 == "火星")) and aspect_type == "四分相":
                    ominous_config = OMINOUS_EVENTS["mars_square_saturn"]
                    events.append({
                        "type": "aspect_event",
                        "event_key": "mars_square_saturn",
                        "name": ominous_config["name"],
                        "planets": ominous_config["planets"],
                        "icon": ominous_config["icon"],
                        "severity": ominous_config["severity"].value,
                        "description": ominous_config["description"],
                        "affected_areas": ominous_config["affected_areas"],
                        "recommendations": ominous_config["recommendations"],
                        "aspect_type": aspect_type,
                        "is_ominous": True,
                        "is_warning": True,
                        "is_critical": True
                    })
                
                elif ((p1 == "天王星" and p2 == "冥王星") or (p1 == "冥王星" and p2 == "天王星")) and aspect_type == "四分相":
                    ominous_config = OMINOUS_EVENTS["uranus_square_pluto"]
                    events.append({
                        "type": "aspect_event",
                        "event_key": "uranus_square_pluto",
                        "name": ominous_config["name"],
                        "planets": ominous_config["planets"],
                        "icon": ominous_config["icon"],
                        "severity": ominous_config["severity"].value,
                        "description": ominous_config["description"],
                        "affected_areas": ominous_config["affected_areas"],
                        "recommendations": ominous_config["recommendations"],
                        "aspect_type": aspect_type,
                        "is_ominous": True,
                        "is_warning": True,
                        "is_critical": True
                    })
            
            events.sort(key=lambda x: {
                WeatherSeverity.CRITICAL.value: 5,
                WeatherSeverity.SEVERE.value: 4,
                WeatherSeverity.MODERATE.value: 3,
                WeatherSeverity.MILD.value: 2,
                WeatherSeverity.CLEAR.value: 1
            }.get(x.get("severity", WeatherSeverity.MILD.value), 1), reverse=True)
            
        except Exception as e:
            logger.error(f"检测天象事件失败: {e}")
        
        return events
    
    def calculate_hourly_energy(self, db: Session) -> EnergyWeatherSnapshot:
        """
        每小时能量统计
        
        统计所有在线用户的星盘 + 天象夹角，计算全场能量值
        """
        now = datetime.utcnow()
        
        online_users = community_energy_service.get_online_users(db, scope="global")
        online_count = len(online_users)
        
        planet_distribution = community_energy_service.aggregate_planet_distribution(db, online_users)
        aspect_distribution = community_energy_service.aggregate_aspect_distribution(db, online_users)
        
        users_with_chart = planet_distribution.get("total_users", 0)
        
        collective_energy = community_energy_service.calculate_community_energy(
            db, online_users, aspect_distribution
        )
        
        overall_score = collective_energy.get("overall_score", 50.0)
        overall_mood = collective_energy.get("overall_mood", "neutral")
        overall_mood_label = collective_energy.get("overall_mood_label", "平稳")
        
        ominous_events = self.detect_current_transit_events(db)
        
        has_warning = any(e.get("is_warning", False) for e in ominous_events)
        has_critical = any(e.get("is_critical", False) for e in ominous_events)
        
        weather_severity = self._determine_weather_severity(
            overall_score, overall_mood, has_warning, has_critical, ominous_events
        )
        
        weather_config = WEATHER_SEVERITY_CONFIG[weather_severity]
        
        jd, _ = ephemeris.local_time_to_julday(
            now.year, now.month, now.day,
            now.hour, now.minute,
            39.9042, 116.4074
        )
        moon_phase = calculate_moon_phase(jd)
        mercury_status = check_mercury_retrograde(jd)
        
        transit_planets = ephemeris.calculate_multiple_planets(jd, MAIN_PLANETS)
        transit_aspects = ephemeris.calculate_all_aspects(transit_planets, transit_planets)
        
        snapshot_id = f"weather_{now.strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"
        
        snapshot = EnergyWeatherSnapshot(
            snapshot_id=snapshot_id,
            timestamp=now,
            
            overall_energy_score=overall_score,
            collective_mood=overall_mood,
            collective_mood_label=overall_mood_label,
            
            weather_severity=weather_severity,
            weather_label=weather_config["label"],
            weather_icon=weather_config["icon"],
            
            online_user_count=online_count,
            users_with_chart=users_with_chart,
            
            dominant_planets=planet_distribution.get("dominant_planets", []),
            dominant_aspects=aspect_distribution.get("dominant_aspects", []),
            
            ominous_events=ominous_events,
            has_warning=has_warning,
            warning_level="critical" if has_critical else "severe" if has_warning else "none",
            
            dimension_energies=collective_energy.get("dimensions", []),
            
            moon_phase=moon_phase,
            mercury_status=mercury_status,
            
            transit_aspects=transit_aspects[:10]
        )
        
        triggered_missions = self._generate_missions_for_mood(
            overall_mood, weather_severity, has_warning
        )
        snapshot.triggered_missions = triggered_missions
        
        self._last_snapshot = snapshot
        self._snapshot_history.append(snapshot)
        if len(self._snapshot_history) > self._max_history_size:
            self._snapshot_history.pop(0)
        
        logger.info(
            f"能量气象站快照已生成: ID={snapshot_id}, "
            f"在线用户={online_count}, 能量分数={overall_score}, "
            f"天气={weather_config['label']}, 预警={has_warning}"
        )
        
        return snapshot
    
    def _determine_weather_severity(
        self,
        overall_score: float,
        overall_mood: str,
        has_warning: bool,
        has_critical: bool,
        ominous_events: List[Dict[str, Any]]
    ) -> WeatherSeverity:
        """
        根据能量分数和凶星天象确定天气严重程度
        """
        if has_critical:
            return WeatherSeverity.CRITICAL
        
        if has_warning:
            severe_count = sum(
                1 for e in ominous_events 
                if e.get("severity") == WeatherSeverity.SEVERE.value
            )
            if severe_count >= 2:
                return WeatherSeverity.CRITICAL
            return WeatherSeverity.SEVERE
        
        if overall_mood == "harmonious":
            if overall_score >= 75:
                return WeatherSeverity.CLEAR
            else:
                return WeatherSeverity.MILD
        elif overall_mood == "challenging":
            if overall_score < 30:
                return WeatherSeverity.MODERATE
            else:
                return WeatherSeverity.MILD
        elif overall_mood == "tense":
            if overall_score < 40:
                return WeatherSeverity.MODERATE
            else:
                return WeatherSeverity.MILD
        else:
            if overall_score >= 60:
                return WeatherSeverity.MILD
            elif overall_score >= 40:
                return WeatherSeverity.MILD
            else:
                return WeatherSeverity.MODERATE
    
    def _generate_missions_for_mood(
        self,
        mood: str,
        weather_severity: WeatherSeverity,
        has_warning: bool
    ) -> List[Dict[str, Any]]:
        """
        根据集体情绪生成暖心小任务
        """
        missions = []
        
        if has_warning or weather_severity in [WeatherSeverity.SEVERE, WeatherSeverity.CRITICAL]:
            mission_pool = WARM_MISSION_TEMPLATES.get("challenging", [])
        elif mood == "harmonious":
            mission_pool = WARM_MISSION_TEMPLATES.get("harmonious_high", [])
        elif mood == "tense" or mood == "challenging":
            mission_pool = WARM_MISSION_TEMPLATES.get("tense", [])
        else:
            mission_pool = WARM_MISSION_TEMPLATES.get("balanced", [])
        
        if mission_pool:
            selected_count = min(3, len(mission_pool))
            selected = random.sample(mission_pool, selected_count)
            
            for i, mission in enumerate(selected):
                mission_with_id = mission.copy()
                mission_with_id["instance_id"] = f"mission_{datetime.now().strftime('%Y%m%d%H%M')}_{i}_{random.randint(100, 999)}"
                mission_with_id["generated_at"] = datetime.now().isoformat()
                mission_with_id["expires_at"] = (datetime.now() + timedelta(hours=24)).isoformat()
                missions.append(mission_with_id)
        
        return missions
    
    def get_current_weather(self, db: Session) -> Dict[str, Any]:
        """
        获取当前能量天气
        """
        if self._last_snapshot is None:
            snapshot = self.calculate_hourly_energy(db)
        else:
            now = datetime.utcnow()
            time_since_last = (now - self._last_snapshot.timestamp).total_seconds()
            
            if time_since_last > 3600:
                snapshot = self.calculate_hourly_energy(db)
            else:
                snapshot = self._last_snapshot
        
        return self._snapshot_to_dict(snapshot)
    
    def get_weather_history(self, hours: int = 12) -> List[Dict[str, Any]]:
        """
        获取天气历史
        """
        return [
            self._snapshot_to_dict(s) 
            for s in self._snapshot_history[-hours:]
        ]
    
    def _snapshot_to_dict(self, snapshot: EnergyWeatherSnapshot) -> Dict[str, Any]:
        """
        将快照转换为字典
        """
        weather_config = WEATHER_SEVERITY_CONFIG[snapshot.weather_severity]
        
        return {
            "snapshot_id": snapshot.snapshot_id,
            "timestamp": snapshot.timestamp.isoformat(),
            
            "overall_energy_score": snapshot.overall_energy_score,
            "collective_mood": snapshot.collective_mood,
            "collective_mood_label": snapshot.collective_mood_label,
            
            "weather_severity": snapshot.weather_severity.value,
            "weather_label": snapshot.weather_label,
            "weather_icon": snapshot.weather_icon,
            "weather_color": weather_config["color"],
            "weather_bg_color": weather_config["bg_color"],
            "weather_description": weather_config["description"],
            
            "online_user_count": snapshot.online_user_count,
            "users_with_chart": snapshot.users_with_chart,
            
            "dominant_planets": snapshot.dominant_planets,
            "dominant_aspects": snapshot.dominant_aspects,
            
            "ominous_events": snapshot.ominous_events,
            "has_warning": snapshot.has_warning,
            "warning_level": snapshot.warning_level,
            "is_critical": snapshot.weather_severity == WeatherSeverity.CRITICAL,
            
            "dimension_energies": snapshot.dimension_energies,
            
            "moon_phase": snapshot.moon_phase,
            "mercury_status": snapshot.mercury_status,
            
            "transit_aspects": snapshot.transit_aspects,
            
            "triggered_missions": snapshot.triggered_missions
        }
    
    def get_available_contribution_types(self) -> List[Dict[str, Any]]:
        """
        获取可用的能量贡献类型
        """
        return [
            {
                "type": key,
                "name": config["name"],
                "planet": config["planet"],
                "icon": config["icon"],
                "color": config["color"],
                "description": config["description"],
                "base_energy": config["base_energy"],
                "cost_stardust": config["cost_stardust"],
                "duration_minutes": config["duration_minutes"],
                "target_dimensions": config["target_dimensions"]
            }
            for key, config in ENERGY_CONTRIBUTION_TYPES.items()
        ]


energy_weather_service = EnergyWeatherService()


def get_energy_weather_service() -> EnergyWeatherService:
    """获取能量气象站服务单例"""
    return energy_weather_service
