import logging
import json
from decimal import Decimal
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func
from sqlalchemy.exc import SQLAlchemyError

from app.models import (
    User,
    Chart,
    StarDustTransaction,
    ProphecyTicket,
    ResonancePoolSnapshot,
    ResonanceContribution
)
from app.services.classical_astrology_service import (
    get_classical_astrology_service,
    ClassicalAstrologyService
)
from app.services.profile_extractor_service import (
    extract_element_distribution,
    extract_stelliums,
    get_planet_weight,
    PlanetWeight
)
from app.astro import ELEMENTS, ZODIAC_SIGNS

logger = logging.getLogger(__name__)


class ElementType(str, Enum):
    FIRE = "fire"
    EARTH = "earth"
    AIR = "air"
    WATER = "water"


ELEMENT_INFO = {
    ElementType.FIRE: {
        "name_cn": "火象",
        "signs": ["白羊座", "狮子座", "射手座"],
        "color": "#EF4444",
        "glow_color": "#FCA5A5",
        "effects": {
            "action_bonus": 1.0,
            "crit_bonus": 0.1,
            "description": "火象能量注入：提升全服行动力与暴击率"
        }
    },
    ElementType.EARTH: {
        "name_cn": "土象",
        "signs": ["金牛座", "处女座", "摩羯座"],
        "color": "#84CC16",
        "glow_color": "#D9F99D",
        "effects": {
            "stability_bonus": 1.0,
            "endurance_bonus": 0.15,
            "description": "土象能量注入：提升稳定度与持久力"
        }
    },
    ElementType.AIR: {
        "name_cn": "风象",
        "signs": ["双子座", "天秤座", "水瓶座"],
        "color": "#3B82F6",
        "glow_color": "#93C5FD",
        "effects": {
            "communication_bonus": 1.0,
            "thinking_bonus": 0.12,
            "description": "风象能量注入：提升沟通能力与思维敏捷度"
        }
    },
    ElementType.WATER: {
        "name_cn": "水象",
        "signs": ["巨蟹座", "天蝎座", "双鱼座"],
        "color": "#8B5CF6",
        "glow_color": "#C4B5FD",
        "effects": {
            "healing_bonus": 1.0,
            "match_bonus": 0.08,
            "description": "水象能量注入：提升治愈能力与缘分匹配概率"
        }
    }
}


ELEMENT_INFO_SERIALIZABLE = {
    "fire": {
        "name_cn": "火象",
        "signs": ["白羊座", "狮子座", "射手座"],
        "color": "#EF4444",
        "glow_color": "#FCA5A5",
        "effects": {
            "action_bonus": 1.0,
            "crit_bonus": 0.1,
            "description": "火象能量注入：提升全服行动力与暴击率"
        }
    },
    "earth": {
        "name_cn": "土象",
        "signs": ["金牛座", "处女座", "摩羯座"],
        "color": "#84CC16",
        "glow_color": "#D9F99D",
        "effects": {
            "stability_bonus": 1.0,
            "endurance_bonus": 0.15,
            "description": "土象能量注入：提升稳定度与持久力"
        }
    },
    "air": {
        "name_cn": "风象",
        "signs": ["双子座", "天秤座", "水瓶座"],
        "color": "#3B82F6",
        "glow_color": "#93C5FD",
        "effects": {
            "communication_bonus": 1.0,
            "thinking_bonus": 0.12,
            "description": "风象能量注入：提升沟通能力与思维敏捷度"
        }
    },
    "water": {
        "name_cn": "水象",
        "signs": ["巨蟹座", "天蝎座", "双鱼座"],
        "color": "#8B5CF6",
        "glow_color": "#C4B5FD",
        "effects": {
            "healing_bonus": 1.0,
            "match_bonus": 0.08,
            "description": "水象能量注入：提升治愈能力与缘分匹配概率"
        }
    }
}


class ResonanceTier(str, Enum):
    DORMANT = "dormant"
    AWAKENING = "awakening"
    GLOWING = "glowing"
    RADIANT = "radiant"
    TRANSCENDENT = "transcendent"


TIER_CONFIG = {
    ResonanceTier.DORMANT: {
        "name_cn": "沉寂",
        "min_energy": Decimal("0"),
        "max_energy": Decimal("1000"),
        "ticket_reward": 0,
        "nebula_intensity": Decimal("0.1")
    },
    ResonanceTier.AWAKENING: {
        "name_cn": "觉醒",
        "min_energy": Decimal("1000"),
        "max_energy": Decimal("10000"),
        "ticket_reward": 5,
        "nebula_intensity": Decimal("0.3")
    },
    ResonanceTier.GLOWING: {
        "name_cn": "辉光",
        "min_energy": Decimal("10000"),
        "max_energy": Decimal("50000"),
        "ticket_reward": 10,
        "nebula_intensity": Decimal("0.5")
    },
    ResonanceTier.RADIANT: {
        "name_cn": "璀璨",
        "min_energy": Decimal("50000"),
        "max_energy": Decimal("200000"),
        "ticket_reward": 20,
        "nebula_intensity": Decimal("0.75")
    },
    ResonanceTier.TRANSCENDENT: {
        "name_cn": "超凡",
        "min_energy": Decimal("200000"),
        "max_energy": Decimal("999999999999"),
        "ticket_reward": 50,
        "nebula_intensity": Decimal("1.0")
    }
}


TIER_CONFIG_SERIALIZABLE = {
    "dormant": {
        "name_cn": "沉寂",
        "min_energy": 0,
        "max_energy": 1000,
        "ticket_reward": 0,
        "nebula_intensity": 0.1
    },
    "awakening": {
        "name_cn": "觉醒",
        "min_energy": 1000,
        "max_energy": 10000,
        "ticket_reward": 5,
        "nebula_intensity": 0.3
    },
    "glowing": {
        "name_cn": "辉光",
        "min_energy": 10000,
        "max_energy": 50000,
        "ticket_reward": 10,
        "nebula_intensity": 0.5
    },
    "radiant": {
        "name_cn": "璀璨",
        "min_energy": 50000,
        "max_energy": 200000,
        "ticket_reward": 20,
        "nebula_intensity": 0.75
    },
    "transcendent": {
        "name_cn": "超凡",
        "min_energy": 200000,
        "max_energy": 999999999999,
        "ticket_reward": 50,
        "nebula_intensity": 1.0
    }
}


BASE_FRAGMENT_COST = 10
DECIMAL_ZERO = Decimal("0")
DECIMAL_ONE = Decimal("1")


@dataclass
class StrongPlanet:
    name: str
    sign: str
    element: ElementType
    dignity_score: int
    weight: int
    multiplier: float = 1.0
    is_stellium: bool = False


@dataclass
class RefineResult:
    success: bool
    error_message: str = ""
    selected_planet: Optional[StrongPlanet] = None
    strong_planets: List[StrongPlanet] = field(default_factory=list)
    fragment_cost: int = 0
    base_energy: float = 0.0
    total_energy: float = 0.0
    element: Optional[ElementType] = None
    multiplier: float = 1.0


@dataclass
class PoolStatus:
    current_tier: str
    current_energy: float
    tier_progress: float
    element_distribution: Dict[str, float]
    nebula_color: str
    nebula_intensity: float
    active_effects: Dict[str, Any]
    next_tier: Optional[Dict[str, Any]] = None
    tickets_pending: int = 0


class ResonanceAuditLog:
    def __init__(self, db: Session, user_id: int, action: str):
        self.db = db
        self.user_id = user_id
        self.action = action
        self.start_time = datetime.utcnow()
        self.details = {}
    
    def add_detail(self, key: str, value: Any):
        self.details[key] = value
    
    def log_success(self, result: Any = None):
        self._save_log(status="success", result=result)
    
    def log_failure(self, error: str):
        self._save_log(status="failed", error=error)
    
    def _save_log(self, status: str, result: Any = None, error: str = None):
        try:
            audit_data = {
                "action": self.action,
                "user_id": self.user_id,
                "status": status,
                "duration_ms": int((datetime.utcnow() - self.start_time).total_seconds() * 1000),
                "details": self.details,
                "created_at": self.start_time.isoformat()
            }
            if result is not None:
                audit_data["result"] = str(result)[:500]
            if error is not None:
                audit_data["error"] = str(error)[:500]
            
            logger.info(f"[AUDIT] {json.dumps(audit_data, ensure_ascii=False, default=str)}")
        except Exception as e:
            logger.error(f"审计日志记录失败: {e}")


class StarResonanceService:
    _instance: Optional['StarResonanceService'] = None
    _classical_service: Optional[ClassicalAstrologyService] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def _get_classical_service(self) -> ClassicalAstrologyService:
        if self._classical_service is None:
            self._classical_service = get_classical_astrology_service()
        return self._classical_service
    
    def _safe_decimal(self, value) -> Decimal:
        if value is None:
            return DECIMAL_ZERO
        if isinstance(value, Decimal):
            return value
        try:
            return Decimal(str(value))
        except:
            return DECIMAL_ZERO
    
    def get_user_chart(self, db: Session, user_id: int) -> Optional[Dict[str, Any]]:
        try:
            chart = db.query(Chart).options(
                joinedload(Chart.user)
            ).filter(Chart.user_id == user_id).order_by(Chart.id.desc()).first()
            
            if not chart:
                return None
            
            try:
                chart_data = json.loads(chart.chart_data) if chart.chart_data else {}
                return chart_data
            except Exception as e:
                logger.error(f"解析用户星盘数据失败: {e}")
                return None
        except Exception as e:
            logger.error(f"获取用户星盘失败: {e}")
            return None
    
    def _get_default_strong_planets(self) -> List[StrongPlanet]:
        default_planets = [
            {
                "name": "太阳",
                "sign": "狮子座",
                "element": ElementType.FIRE,
                "dignity_score": 5,
                "weight": 10,
                "is_stellium": False
            },
            {
                "name": "月亮",
                "sign": "巨蟹座",
                "element": ElementType.WATER,
                "dignity_score": 5,
                "weight": 10,
                "is_stellium": False
            },
            {
                "name": "水星",
                "sign": "双子座",
                "element": ElementType.AIR,
                "dignity_score": 5,
                "weight": 7,
                "is_stellium": False
            },
            {
                "name": "金星",
                "sign": "金牛座",
                "element": ElementType.EARTH,
                "dignity_score": 5,
                "weight": 7,
                "is_stellium": False
            },
            {
                "name": "火星",
                "sign": "白羊座",
                "element": ElementType.FIRE,
                "dignity_score": 5,
                "weight": 7,
                "is_stellium": False
            }
        ]
        
        result = []
        for p in default_planets:
            multiplier = 1.0
            multiplier += p["dignity_score"] / 50.0
            multiplier += p["weight"] / 50.0
            if p["is_stellium"]:
                multiplier += 0.5
            
            result.append(StrongPlanet(
                name=p["name"],
                sign=p["sign"],
                element=p["element"],
                dignity_score=p["dignity_score"],
                weight=p["weight"],
                multiplier=round(multiplier, 2),
                is_stellium=p["is_stellium"]
            ))
        
        result.sort(key=lambda p: p.multiplier, reverse=True)
        return result
    
    def analyze_strong_planets(self, chart_data: Dict[str, Any]) -> List[StrongPlanet]:
        strong_planets: List[StrongPlanet] = []
        planets = chart_data.get("planets", [])
        
        if not planets:
            return self._get_default_strong_planets()
        
        classical_service = self._get_classical_service()
        stelliums = extract_stelliums(planets)
        stellium_signs = {s["sign"] for s in stelliums if s.get("count", 0) >= 3}
        
        main_planets_names = ["太阳", "月亮", "水星", "金星", "火星", "木星", "土星", "天王星", "海王星", "冥王星"]
        main_planets = [p for p in planets if p.get("name") in main_planets_names]
        
        if not main_planets:
            return self._get_default_strong_planets()
        
        for planet in main_planets:
            try:
                planet_name = planet.get("name", "")
                zodiac = planet.get("zodiac", {})
                planet_sign = zodiac.get("sign", "")
                planet_degree = zodiac.get("degree", 0)
                
                if not planet_name or not planet_sign:
                    continue
                
                dignity_score = 0
                try:
                    dignity = classical_service.get_planet_dignity(
                        planet_name=planet_name,
                        sign_name=planet_sign,
                        degree=planet_degree
                    )
                    dignity_score = dignity.score if dignity else 0
                except Exception as e:
                    logger.warning(f"计算庙旺弱陷失败: {planet_name} - {e}")
                
                weight_enum = get_planet_weight(planet_name)
                weight = weight_enum.value if hasattr(weight_enum, 'value') else weight_enum
                
                element = self._get_planet_element(planet_sign)
                if element is None:
                    continue
                
                multiplier = 1.0
                multiplier += dignity_score / 50.0
                weight_val = float(weight) if weight else 0.0
                multiplier += weight_val / 50.0
                
                is_stellium = planet_sign in stellium_signs
                if is_stellium:
                    multiplier += 0.5
                
                strong_planets.append(StrongPlanet(
                    name=planet_name,
                    sign=planet_sign,
                    element=element,
                    dignity_score=dignity_score,
                    weight=int(weight) if weight else 0,
                    multiplier=round(multiplier, 2),
                    is_stellium=is_stellium
                ))
                
            except Exception as e:
                logger.error(f"分析行星数据失败: {e}")
                continue
        
        if not strong_planets:
            return self._get_default_strong_planets()
        
        strong_planets.sort(key=lambda p: p.multiplier, reverse=True)
        return strong_planets
    
    def _get_planet_element(self, sign_name: str) -> Optional[ElementType]:
        element_map = {
            "白羊座": ElementType.FIRE,
            "狮子座": ElementType.FIRE,
            "射手座": ElementType.FIRE,
            "金牛座": ElementType.EARTH,
            "处女座": ElementType.EARTH,
            "摩羯座": ElementType.EARTH,
            "双子座": ElementType.AIR,
            "天秤座": ElementType.AIR,
            "水瓶座": ElementType.AIR,
            "巨蟹座": ElementType.WATER,
            "天蝎座": ElementType.WATER,
            "双鱼座": ElementType.WATER
        }
        return element_map.get(sign_name)
    
    def refine_energy(
        self,
        db: Session,
        user_id: int,
        fragment_amount: int,
        selected_planet_name: Optional[str] = None
    ) -> RefineResult:
        audit = ResonanceAuditLog(db, user_id, "refine_energy_preview")
        audit.add_detail("fragment_amount", fragment_amount)
        audit.add_detail("selected_planet_name", selected_planet_name)
        
        try:
            if fragment_amount < BASE_FRAGMENT_COST:
                result = RefineResult(
                    success=False,
                    error_message=f"星元碎片数量不足，基础消耗为 {BASE_FRAGMENT_COST}"
                )
                audit.log_failure(result.error_message)
                return result
            
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                result = RefineResult(success=False, error_message="用户不存在")
                audit.log_failure(result.error_message)
                return result
            
            if (user.stardust_fragment_balance or 0) < fragment_amount:
                result = RefineResult(
                    success=False,
                    error_message=f"星元碎片不足，当前余额: {user.stardust_fragment_balance or 0}"
                )
                audit.log_failure(result.error_message)
                return result
            
            chart_data = self.get_user_chart(db, user_id)
            if not chart_data:
                result = RefineResult(success=False, error_message="未找到您的星盘数据")
                audit.log_failure(result.error_message)
                return result
            
            strong_planets = self.analyze_strong_planets(chart_data)
            if not strong_planets:
                result = RefineResult(success=False, error_message="未发现可用于炼化的行星")
                audit.log_failure(result.error_message)
                return result
            
            selected_planet = None
            if selected_planet_name:
                for planet in strong_planets:
                    if planet.name == selected_planet_name:
                        selected_planet = planet
                        break
                
                if not selected_planet:
                    selected_planet = strong_planets[0]
            else:
                selected_planet = strong_planets[0]
            
            base_energy = float(fragment_amount) * 1.0
            total_energy = base_energy * selected_planet.multiplier
            
            result = RefineResult(
                success=True,
                selected_planet=selected_planet,
                strong_planets=strong_planets,
                fragment_cost=fragment_amount,
                base_energy=round(base_energy, 2),
                total_energy=round(total_energy, 2),
                element=selected_planet.element,
                multiplier=selected_planet.multiplier
            )
            
            audit.add_detail("planet", selected_planet.name)
            audit.add_detail("element", selected_planet.element.value)
            audit.add_detail("multiplier", selected_planet.multiplier)
            audit.add_detail("total_energy", total_energy)
            audit.log_success()
            
            return result
            
        except Exception as e:
            logger.error(f"炼化预览失败: {e}")
            result = RefineResult(success=False, error_message=f"炼化失败: {str(e)}")
            audit.log_failure(str(e))
            return result
    
    def contribute_to_pool(
        self,
        db: Session,
        user_id: int,
        refine_result: RefineResult
    ) -> Dict[str, Any]:
        audit = ResonanceAuditLog(db, user_id, "contribute_to_pool")
        audit.add_detail("fragment_cost", refine_result.fragment_cost)
        audit.add_detail("planet", refine_result.selected_planet.name if refine_result.selected_planet else None)
        
        try:
            if not refine_result.success:
                return {
                    "success": False,
                    "error": refine_result.error_message
                }
            
            if not refine_result.selected_planet:
                return {
                    "success": False,
                    "error": "未选择炼化行星"
                }
            
            db.begin_nested()
            
            try:
                user = db.query(User).filter(User.id == user_id).with_for_update().first()
                if not user:
                    db.rollback()
                    return {"success": False, "error": "用户不存在"}
                
                fragment_cost = refine_result.fragment_cost
                if (user.stardust_fragment_balance or 0) < fragment_cost:
                    db.rollback()
                    return {
                        "success": False,
                        "error": f"星元碎片不足，当前余额: {user.stardust_fragment_balance or 0}"
                    }
                
                balance_before = user.stardust_fragment_balance or 0
                balance_after = balance_before - fragment_cost
                
                transaction = StarDustTransaction(
                    user_id=user_id,
                    transaction_type="resonance_contribution",
                    currency_type="fragment",
                    amount=-fragment_cost,
                    balance_before=balance_before,
                    balance_after=balance_after,
                    description=f"星能共鸣池炼化注入 - {refine_result.selected_planet.name}在{refine_result.selected_planet.sign}",
                    created_at=datetime.utcnow()
                )
                db.add(transaction)
                db.flush()
                
                user.stardust_fragment_balance = balance_after
                
                planet = refine_result.selected_planet
                contribution = ResonanceContribution(
                    user_id=user_id,
                    element=planet.element.value,
                    planet_name=planet.name,
                    planet_sign=planet.sign,
                    fragment_cost=fragment_cost,
                    base_energy=refine_result.base_energy,
                    total_energy=refine_result.total_energy,
                    energy_multiplier=planet.multiplier,
                    dignity_score=planet.dignity_score,
                    is_stellium=planet.is_stellium,
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                db.add(contribution)
                db.flush()
                
                snapshot = self._update_pool_atomic(
                    db,
                    planet.element,
                    refine_result.total_energy
                )
                
                tickets_awarded = self._check_and_award_tiers(db, snapshot, user_id)
                
                pool_status = self._get_pool_status_dict(snapshot)
                
                db.commit()
                
                audit.add_detail("contribution_id", contribution.id)
                audit.add_detail("tickets_awarded", tickets_awarded)
                audit.log_success()
                
                element_info = ELEMENT_INFO_SERIALIZABLE.get(planet.element.value, {})
                
                return {
                    "success": True,
                    "message": f"能量注入成功！{f'获得 {tickets_awarded} 张预言券' if tickets_awarded > 0 else ''}",
                    "contribution": {
                        "id": contribution.id,
                        "element": planet.element.value,
                        "element_name": element_info.get("name_cn", ""),
                        "planet_name": planet.name,
                        "planet_sign": planet.sign,
                        "fragment_cost": fragment_cost,
                        "total_energy": refine_result.total_energy
                    },
                    "pool_status": pool_status,
                    "tickets_awarded": tickets_awarded,
                    "transaction": {
                        "id": transaction.id,
                        "balance_before": balance_before,
                        "balance_after": balance_after
                    }
                }
                
            except SQLAlchemyError as e:
                db.rollback()
                logger.error(f"数据库事务失败: {e}")
                audit.log_failure(str(e))
                return {
                    "success": False,
                    "error": f"数据库错误: {str(e)}"
                }
                
        except Exception as e:
            logger.error(f"注入能量池失败: {e}")
            audit.log_failure(str(e))
            return {
                "success": False,
                "error": f"注入失败: {str(e)}"
            }
    
    def _update_pool_atomic(
        self,
        db: Session,
        element: ElementType,
        energy: float
    ) -> ResonancePoolSnapshot:
        now = datetime.utcnow()
        
        latest = db.query(ResonancePoolSnapshot).order_by(
            ResonancePoolSnapshot.snapshot_at.desc()
        ).with_for_update().first()
        
        if latest:
            element_dist = json.loads(latest.element_distribution) if latest.element_distribution else {}
        else:
            element_dist = {
                "fire": 0.0,
                "earth": 0.0,
                "air": 0.0,
                "water": 0.0
            }
        
        element_key = element.value
        current_elem_energy = element_dist.get(element_key, 0.0)
        element_dist[element_key] = float(current_elem_energy) + float(energy)
        
        total_energy = sum(float(v) for v in element_dist.values())
        
        current_tier = self._calculate_tier(total_energy)
        tier_config = TIER_CONFIG[current_tier]
        
        progress_min = float(tier_config["min_energy"])
        progress_max = float(tier_config["max_energy"])
        tier_progress = 0.0
        
        if progress_max > progress_min:
            tier_progress = (total_energy - progress_min) / (progress_max - progress_min)
            tier_progress = min(max(tier_progress, 0.0), 1.0)
        
        nebula_color = self._calculate_nebula_color(element_dist)
        
        snapshot = ResonancePoolSnapshot(
            total_energy=total_energy,
            current_tier=current_tier.value,
            tier_progress=tier_progress,
            element_distribution=json.dumps(element_dist, ensure_ascii=False),
            nebula_color=nebula_color,
            nebula_intensity=float(tier_config["nebula_intensity"]),
            active_effects=json.dumps(self._calculate_active_effects(element_dist), ensure_ascii=False, default=str),
            snapshot_at=now,
            created_at=now
        )
        
        db.add(snapshot)
        db.flush()
        
        return snapshot
    
    def _calculate_tier(self, total_energy: float) -> ResonanceTier:
        for tier in reversed(ResonanceTier):
            config = TIER_CONFIG[tier]
            if total_energy >= float(config["min_energy"]):
                return tier
        return ResonanceTier.DORMANT
    
    def _calculate_nebula_color(self, element_dist: Dict[str, float]) -> str:
        total = sum(float(v) for v in element_dist.values())
        if total <= 0:
            return "#1F2937"
        
        r_total = 0.0
        g_total = 0.0
        b_total = 0.0
        
        for elem_key, energy in element_dist.items():
            energy_val = float(energy)
            if energy_val <= 0:
                continue
            
            ratio = energy_val / total
            
            elem_info = ELEMENT_INFO_SERIALIZABLE.get(elem_key, {})
            hex_color = elem_info.get("color", "#1F2937").lstrip('#')
            
            try:
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
                
                r_total += r * ratio
                g_total += g * ratio
                b_total += b * ratio
            except Exception as e:
                logger.warning(f"计算星云颜色时跳过无效元素: {elem_key}")
                continue
        
        if r_total == 0 and g_total == 0 and b_total == 0:
            return "#1F2937"
        
        final_r = int(round(r_total))
        final_g = int(round(g_total))
        final_b = int(round(b_total))
        
        final_r = max(0, min(255, final_r))
        final_g = max(0, min(255, final_g))
        final_b = max(0, min(255, final_b))
        
        return f"#{final_r:02x}{final_g:02x}{final_b:02x}"
    
    def _calculate_active_effects(self, element_dist: Dict[str, float]) -> Dict[str, Any]:
        total = sum(float(v) for v in element_dist.values())
        if total <= 0:
            return {}
        
        effects = {}
        max_ratio = 0.0
        dominant_element = None
        
        for elem_key, energy in element_dist.items():
            energy_val = float(energy)
            if energy_val <= 0:
                continue
            
            ratio = energy_val / total
            
            elem_info = ELEMENT_INFO_SERIALIZABLE.get(elem_key, {})
            
            if ratio > max_ratio:
                max_ratio = ratio
                dominant_element = elem_key
            
            elem_effects = elem_info.get("effects", {})
            effects[elem_key] = {
                "name": elem_info.get("name_cn", ""),
                "energy": energy_val,
                "ratio": ratio * 100,
                "effects": {k: v for k, v in elem_effects.items() if k != "description"}
            }
        
        if dominant_element:
            effects["dominant"] = dominant_element
        
        return effects
    
    def _check_and_award_tiers(
        self,
        db: Session,
        snapshot: ResonancePoolSnapshot,
        contributing_user_id: int
    ) -> int:
        latest = db.query(ResonancePoolSnapshot).order_by(
            ResonancePoolSnapshot.snapshot_at.desc()
        ).offset(1).first()
        
        if not latest:
            return 0
        
        try:
            prev_tier = ResonanceTier(latest.current_tier)
            current_tier = ResonanceTier(snapshot.current_tier)
        except:
            return 0
        
        tier_order = list(ResonanceTier)
        prev_index = tier_order.index(prev_tier)
        current_index = tier_order.index(current_tier)
        
        if current_index <= prev_index:
            return 0
        
        total_tickets = 0
        
        for i in range(prev_index + 1, current_index + 1):
            tier = tier_order[i]
            config = TIER_CONFIG[tier]
            ticket_count = config["ticket_reward"]
            
            if ticket_count > 0:
                existing = db.query(ProphecyTicket).filter(
                    ProphecyTicket.user_id == contributing_user_id,
                    ProphecyTicket.source_snapshot_id == snapshot.id,
                    ProphecyTicket.ticket_type == f"tier_{tier.value}"
                ).first()
                
                if not existing:
                    tickets = self._award_tickets_to_user(
                        db,
                        contributing_user_id,
                        snapshot.id,
                        ticket_count,
                        tier.value
                    )
                    total_tickets += len(tickets)
        
        return total_tickets
    
    def _award_tickets_to_user(
        self,
        db: Session,
        user_id: int,
        snapshot_id: int,
        count: int,
        tier_value: str
    ) -> List[ProphecyTicket]:
        now = datetime.utcnow()
        tickets = []
        
        for _ in range(count):
            ticket = ProphecyTicket(
                user_id=user_id,
                ticket_type=f"tier_{tier_value}",
                source_snapshot_id=snapshot_id,
                is_used=False,
                valid_from=now,
                valid_until=now + timedelta(days=30),
                created_at=now
            )
            db.add(ticket)
            tickets.append(ticket)
        
        db.flush()
        return tickets
    
    def get_pool_status(self, db: Session) -> PoolStatus:
        latest = db.query(ResonancePoolSnapshot).order_by(
            ResonancePoolSnapshot.snapshot_at.desc()
        ).first()
        
        if not latest:
            element_dist = {
                "fire": 0.0,
                "earth": 0.0,
                "air": 0.0,
                "water": 0.0
            }
            
            return PoolStatus(
                current_tier="dormant",
                current_energy=0.0,
                tier_progress=0.0,
                element_distribution=element_dist,
                nebula_color="#1F2937",
                nebula_intensity=0.1,
                active_effects={},
                next_tier={
                    "tier": "awakening",
                    "name": TIER_CONFIG_SERIALIZABLE["awakening"]["name_cn"],
                    "energy_needed": TIER_CONFIG_SERIALIZABLE["awakening"]["min_energy"]
                },
                tickets_pending=0
            )
        
        return self._get_pool_status_from_snapshot(latest, db)
    
    def _get_pool_status_from_snapshot(self, snapshot: ResonancePoolSnapshot, db: Session = None) -> PoolStatus:
        element_dist_raw = json.loads(snapshot.element_distribution) if snapshot.element_distribution else {}
        element_dist = {}
        for key, value in element_dist_raw.items():
            element_dist[key] = float(value)
        
        current_tier_str = snapshot.current_tier
        if current_tier_str not in TIER_CONFIG_SERIALIZABLE:
            current_tier_str = "dormant"
        
        tier_config = TIER_CONFIG_SERIALIZABLE[current_tier_str]
        
        next_tier = None
        tier_order = ["dormant", "awakening", "glowing", "radiant", "transcendent"]
        current_index = tier_order.index(current_tier_str)
        
        if current_index < len(tier_order) - 1:
            next_tier_str = tier_order[current_index + 1]
            next_config = TIER_CONFIG_SERIALIZABLE[next_tier_str]
            current_energy = float(snapshot.total_energy)
            energy_needed = next_config["min_energy"] - current_energy
            next_tier = {
                "tier": next_tier_str,
                "name": next_config["name_cn"],
                "energy_needed": energy_needed
            }
        
        active_effects_raw = json.loads(snapshot.active_effects) if snapshot.active_effects else {}
        active_effects = active_effects_raw
        
        pending_tickets = 0
        if db:
            try:
                pending_tickets = db.query(func.count(ProphecyTicket.id)).filter(
                    ProphecyTicket.user_id != None,
                    ProphecyTicket.is_used == False,
                    ProphecyTicket.valid_until > datetime.utcnow()
                ).scalar() or 0
            except:
                pass
        
        return PoolStatus(
            current_tier=current_tier_str,
            current_energy=float(snapshot.total_energy),
            tier_progress=float(snapshot.tier_progress),
            element_distribution=element_dist,
            nebula_color=snapshot.nebula_color or "#1F2937",
            nebula_intensity=float(snapshot.nebula_intensity),
            active_effects=active_effects,
            next_tier=next_tier,
            tickets_pending=pending_tickets
        )
    
    def _get_pool_status_dict(self, snapshot: ResonancePoolSnapshot) -> Dict[str, Any]:
        status = self._get_pool_status_from_snapshot(snapshot)
        
        element_dist_dict = {}
        for elem_key, energy in status.element_distribution.items():
            info = ELEMENT_INFO_SERIALIZABLE.get(elem_key, {})
            element_dist_dict[elem_key] = {
                "name": info.get("name_cn", ""),
                "energy": energy,
                "color": info.get("color", "#1F2937")
            }
        
        return {
            "current_tier": status.current_tier,
            "current_tier_name": TIER_CONFIG_SERIALIZABLE.get(status.current_tier, {}).get("name_cn", "未知"),
            "current_energy": status.current_energy,
            "tier_progress": status.tier_progress,
            "element_distribution": element_dist_dict,
            "nebula": {
                "color": status.nebula_color,
                "intensity": status.nebula_intensity
            },
            "active_effects": status.active_effects,
            "next_tier": status.next_tier
        }
    
    def get_user_tickets(
        self,
        db: Session,
        user_id: int,
        only_valid: bool = True,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        query = db.query(ProphecyTicket).filter(ProphecyTicket.user_id == user_id)
        
        if only_valid:
            query = query.filter(
                ProphecyTicket.is_used == False,
                ProphecyTicket.valid_until > datetime.utcnow()
            )
        
        tickets = query.order_by(
            ProphecyTicket.created_at.desc()
        ).limit(limit).all()
        
        result = []
        for ticket in tickets:
            result.append({
                "id": ticket.id,
                "ticket_type": ticket.ticket_type,
                "is_used": ticket.is_used,
                "used_at": ticket.used_at.isoformat() if ticket.used_at else None,
                "valid_from": ticket.valid_from.isoformat() if ticket.valid_from else None,
                "valid_until": ticket.valid_until.isoformat() if ticket.valid_until else None,
                "created_at": ticket.created_at.isoformat() if ticket.created_at else None
            })
        
        return result
    
    def get_recent_contributions(
        self,
        db: Session,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        try:
            contributions = db.query(ResonanceContribution).options(
                joinedload(ResonanceContribution.user)
            ).order_by(
                ResonanceContribution.created_at.desc()
            ).limit(limit).all()
            
            result = []
            for contrib in contributions:
                username = None
                if contrib.user:
                    username = contrib.user.username
                
                element_name = None
                if contrib.element:
                    elem_info = ELEMENT_INFO_SERIALIZABLE.get(contrib.element, {})
                    element_name = elem_info.get("name_cn")
                
                result.append({
                    "id": contrib.id,
                    "username": username,
                    "element": contrib.element,
                    "element_name": element_name,
                    "planet_name": contrib.planet_name,
                    "planet_sign": contrib.planet_sign,
                    "fragment_cost": contrib.fragment_cost,
                    "total_energy": contrib.total_energy,
                    "energy_multiplier": contrib.energy_multiplier,
                    "dignity_score": contrib.dignity_score,
                    "is_stellium": contrib.is_stellium,
                    "created_at": contrib.created_at.isoformat() if contrib.created_at else None
                })
            
            return result
            
        except Exception as e:
            logger.error(f"获取最近注入记录失败: {e}")
            return []
    
    def get_element_and_tier_info(self) -> Dict[str, Any]:
        return {
            "elements": ELEMENT_INFO_SERIALIZABLE,
            "tier_config": TIER_CONFIG_SERIALIZABLE
        }


star_resonance_service = StarResonanceService()


def get_star_resonance_service() -> StarResonanceService:
    return star_resonance_service
